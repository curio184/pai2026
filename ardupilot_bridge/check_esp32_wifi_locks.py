"""Reproduce ESP32 lock defects from the actual pinned function bodies.

Uses deterministic recursive-mutex/socket stubs, not hardware or a flight stack.
Writes a review-only minimal patch; never changes the upstream checkout.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PIN="38687117133582049734ebd39f8a7af6f487716a"


def body(text,signature):
    start=text.index(signature);brace=text.index("{",start);level=1;end=brace+1
    while level:
        level+=(text[end]=="{")-(text[end]=="}");end+=1
    return text[start:end]


PREAMBLE=r'''
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <sys/socket.h>
#include <netinet/in.h>
static int task=1;
struct Recursive { int owner=0,depth=0,invalid_gives=0; };
using QueueHandle_t=Recursive*;
constexpr int pdTRUE=1;
constexpr uint32_t portMAX_DELAY=0xffffffffu;
int xSemaphoreTakeRecursive(QueueHandle_t handle,uint32_t) {
    if (handle->depth && handle->owner!=task) { return 0; }
    handle->owner=task;handle->depth++;return pdTRUE;
}
int xSemaphoreGiveRecursive(QueueHandle_t handle) {
    if (!handle->depth || handle->owner!=task) { handle->invalid_gives++;return 0; }
    if (!--handle->depth) { handle->owner=0; }
    return 1;
}
class Semaphore {
public:
    Recursive state;
    void* handle=&state;
    bool give();
    bool take_nonblocking();
    void take_blocking();
};
struct Buffer {
    std::vector<uint8_t> bytes;
    void write(const uint8_t* data,int count) { bytes.insert(bytes.end(),data,data+count); }
};
class WiFiUdpDriver {
public:
    Semaphore _read_mutex;
    int accept_socket=1;
    uint8_t _buffer[512]{};
    Buffer _readbuf;
    bool read_all();
};
static int next_count=-1;
int fake_recvfrom(int,void* data,size_t size,int,struct sockaddr*,socklen_t*) {
    if (next_count>0) { std::memset(data,0x5a,std::min(size,static_cast<size_t>(next_count))); }
    return next_count;
}
#define recvfrom fake_recvfrom
'''

TESTS=r'''
int main() {
    std::vector<std::pair<std::string,bool>> checks;
    {
        Semaphore sem;task=1;
        bool taken=sem.take_nonblocking();
        checks.push_back({"successful_nonblocking_take_retains_ownership",taken && sem.state.owner==1 && sem.state.depth==1});
        task=2;bool other=sem.take_nonblocking();
        checks.push_back({"other_task_cannot_take_held_lock",!other});
        task=1;bool released=sem.give();
        checks.push_back({"one_take_one_release",released && sem.state.depth==0 && sem.state.invalid_gives==0});
    }
    {
        Semaphore sem;task=1;sem.take_nonblocking();sem.take_nonblocking();
        bool twice=sem.state.depth==2;sem.give();
        bool once=sem.state.depth==1;task=2;bool excluded=!sem.take_nonblocking();
        task=1;sem.give();checks.push_back({"recursive_ownership_needs_matching_releases",twice && once && excluded && sem.state.depth==0});
    }
    {
        Semaphore sem;task=1;sem.take_blocking();task=2;
        bool failed=!sem.take_nonblocking();
        checks.push_back({"failed_take_preserves_other_owner",failed && sem.state.owner==1 && sem.state.depth==1 && sem.state.invalid_gives==0});
        task=1;sem.give();
    }
    {
        WiFiUdpDriver driver;task=1;next_count=-1;bool returned=!driver.read_all();
        checks.push_back({"idle_receive_releases_lock",returned && driver._read_mutex.state.depth==0 && driver._read_mutex.state.invalid_gives==0});
    }
    {
        WiFiUdpDriver driver;task=1;next_count=3;bool received=driver.read_all();
        checks.push_back({"datagram_releases_lock_exactly_once",received && driver._read_mutex.state.depth==0 && driver._read_mutex.state.invalid_gives==0});
        checks.push_back({"datagram_payload_preserved",driver._readbuf.bytes==std::vector<uint8_t>({0x5a,0x5a,0x5a})});
    }
    {
        WiFiUdpDriver driver;task=1;next_count=0;bool returned=!driver.read_all();
        checks.push_back({"zero_length_receive_releases_lock",returned && driver._read_mutex.state.depth==0});
    }
    {
        WiFiUdpDriver driver;task=1;bool balanced=true;
        for (int i=0;i<100;i++) {
            next_count=(i%2==0)?-1:2;driver.read_all();
            balanced=balanced && driver._read_mutex.state.depth==0 && driver._read_mutex.state.invalid_gives==0;
        }
        checks.push_back({"alternating_idle_and_packets_remain_balanced",balanced && driver._readbuf.bytes.size()==100});
    }
    bool all=true;std::cout<<"{\"checks\":{";
    for (size_t i=0;i<checks.size();i++) {
        all=all && checks[i].second;
        if (i) { std::cout<<","; }
        std::cout<<"\""<<checks[i].first<<"\":"<<(checks[i].second?"true":"false");
    }
    std::cout<<"},\"all_pass\":"<<(all?"true":"false")<<"}\n";
    return all?0:1;
}
'''


def check(repository,output):
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=repository,text=True).strip()!=PIN:
        raise ValueError("Unexpected upstream revision")
    names=["libraries/AP_HAL_ESP32/Semaphores.cpp","libraries/AP_HAL_ESP32/WiFiUdpDriver.cpp"]
    original={name:(repository/name).read_text() for name in names};revised=original.copy()
    sem_signature="bool Semaphore::take_nonblocking()"
    old=body(original[names[0]],sem_signature)
    new='''bool Semaphore::take_nonblocking()
{
    return xSemaphoreTakeRecursive((QueueHandle_t)handle, 0) == pdTRUE;
}'''
    revised[names[0]]=original[names[0]].replace(old,new,1)
    read_signature="bool WiFiUdpDriver::read_all()"
    old=body(original[names[1]],read_signature)
    new='''bool WiFiUdpDriver::read_all()
{
    _read_mutex.take_blocking();
    struct sockaddr_in client_addr;
    socklen_t socklen = sizeof(client_addr);
    int count = recvfrom(accept_socket, _buffer, sizeof(_buffer) - 1, 0, (struct sockaddr *)&client_addr, &socklen);
    if (count > 0) {
        _readbuf.write(_buffer, count);
    }
    _read_mutex.give();
    return count > 0;
}'''
    revised[names[1]]=original[names[1]].replace(old,new,1)
    output.mkdir(parents=True,exist_ok=False)
    patch="".join("".join(difflib.unified_diff(original[name].splitlines(keepends=True),revised[name].splitlines(keepends=True),
                                               fromfile="a/"+name,tofile="b/"+name)) for name in names)
    (output/"esp32_wifi_locks.patch").write_text(patch)
    results={};compiler=shutil.which("g++")
    if not compiler:raise FileNotFoundError("g++")
    for label,source in [("before",original),("after",revised)]:
        fragments="\n\n".join([body(source[names[0]],s) for s in ["bool Semaphore::give()","void Semaphore::take_blocking()",sem_signature]]+[body(source[names[1]],read_signature)])
        file=output/(label+".cpp");file.write_text(PREAMBLE+fragments+TESTS)
        binary=output/label
        build=subprocess.run([compiler,"-std=c++17","-O0","-g","-Wall","-Wextra",str(file),"-o",str(binary)],capture_output=True,text=True)
        (output/(label+"_build.log")).write_text(build.stdout+build.stderr)
        if build.returncode:raise RuntimeError(build.stderr)
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        results[label]=dict(exit_code=run.returncode,**json.loads(run.stdout))
    if results["before"]["all_pass"] or not results["after"]["all_pass"]:
        raise RuntimeError("Expected defect reproduction and repair check did not hold")
    report=dict(ardupilot_commit=PIN,source_sha256={name:hashlib.sha256(text.encode()).hexdigest() for name,text in original.items()},
                patched_source_sha256={name:hashlib.sha256(text.encode()).hexdigest() for name,text in revised.items()},
                patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),results=results,
                original_checkout_changed=False,AI_assisted_local_review=True,hardware_flashed=False,
                scope="Exact function bodies compiled with deterministic recursive-mutex/socket stubs. No FreeRTOS scheduling, radio throughput, ISR, hardware or full flight-stack test.",
                upstream_review_or_real_hardware_validation_claimed=False)
    (output/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--ardupilot",type=Path,default=Path.home()/"physical_ai_ardupilot/ardupilot")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();check(args.ardupilot,args.output)
