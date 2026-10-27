// External C ABI around the pinned, unmodified StampFly MuJoCo plant.
#include "plant.hpp"
#include <algorithm>
#include <exception>

extern "C" {
void* sf_create(const char* model, float mass) {
    auto* p = new sils::Plant;
    sils::Plant::Config c;
    c.mass = mass;
    c.noise.enable = true;
    c.noise.seed = 20261023;
    c.noise.white_dt = 1.0f / 600.0f;
    c.batt_model_enable = true;
    // Engineering power allowance, not a measured camera assembly.
    c.avionics_current_a = 0.5f;
    if (!p->init(model, c)) { delete p; return nullptr; }
    p->setStartHeight(0.033f);
    return p;
}
void sf_destroy(void* ptr) { delete static_cast<sils::Plant*>(ptr); }
float sf_hover(void* ptr) { return static_cast<sils::Plant*>(ptr)->hoverDuty(); }
float sf_thrust(void* ptr, float duty) {
    return static_cast<sils::Plant*>(ptr)->dutyToThrust(duty);
}
void sf_step(void* ptr, const double* duty, double dt, double* out) {
    auto& p = *static_cast<sils::Plant*>(ptr);
    sf::MotorOutput cmd{};
    for (int i = 0; i < 4; ++i) cmd.duty[i] = std::clamp(duty[i], 0.0, 1.0);
    p.setDuty(cmd);
    p.step(static_cast<float>(dt));
    const auto t = p.truth();
    const auto imu = p.imu();
    out[0] = p.data()->time;
    out[1] = t.pos_ned.x; out[2] = t.pos_ned.y; out[3] = t.pos_ned.z;
    out[4] = t.vel_ned.x; out[5] = t.vel_ned.y; out[6] = t.vel_ned.z;
    out[7] = t.q_nb.w; out[8] = t.q_nb.x; out[9] = t.q_nb.y; out[10] = t.q_nb.z;
    for (int i = 0; i < 3; ++i) { out[11+i] = imu.gyro[i]; out[14+i] = imu.accel[i]; }
    out[17] = p.batteryVoltage();
    out[18] = p.tof().distance;
    for (int i = 0; i < 7; ++i) out[19+i] = p.data()->qpos[i];
    for (int i = 0; i < 6; ++i) out[26+i] = p.data()->qvel[i];
}
}
