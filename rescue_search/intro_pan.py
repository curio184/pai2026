"""Revised pronunciation plus a survivor reveal; preserve the previous delivered edit."""
import json,hashlib,shutil,sys
from pathlib import Path
import intro_atmosphere as base
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_pan'
DEST=base.ROOT/'output/video/rescue_drone_intro_pan.mp4'
DURATION=base.DURATION;FPS=base.FPS;ROOT=base.ROOT;HEADING=base.HEADING;font=base.font
first=json.loads((OUT/'verified_voice.json').read_text(encoding='utf8'))
second=json.loads((HERE/'intro_slow/generation_manifest.json').read_text(encoding='utf8'))[1]
CAPTIONS=[(4.8,4.8+first['duration_s'],base.CAPTIONS[0][2]),(16.25,16.25+second['duration_s'],base.CAPTIONS[1][2])]
base.OUT=OUT;base.DEST=DEST;base.CAPTIONS=CAPTIONS
Intro=base.Intro

def prepare():
    for name in ['ceiling','rubble']:
        shutil.copytree(HERE/'intro_atmosphere'/name,OUT/name,dirs_exist_ok=True)
    shutil.copy2(HERE/'intro_slow/voice_01.wav',OUT/'voice_01.wav')
    sys.path.insert(0,str(ROOT));import make_rescue_presentation_audio as old
    clips=[]
    for i,(g,start) in enumerate([(first,4.8),(second,16.25)]):
        name=f'voice_{i:02}.wav'
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==g['sha256']
        assert ''.join(CAPTIONS[i][2])==g['text']
        clips.append(dict(index=i,start=start,max_s=9 if i==0 else 7,text=g['text'],caption=g['text'],file=name))
    (OUT/'generation_manifest.json').write_text(json.dumps([first,second],ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    old.TMP=OUT;old.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0),dict(start=4)]);old.mix()
    review=json.loads((OUT/'audio_review.json').read_text())
    review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='No rotor audio added',verbatim_subtitles=True,time_stretch_used=False,
        opening_audio_independently_transcribed=True,opening_words='災害救助ドローンとは')
    (OUT/'audio_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf8')

def render():
    source=json.loads((OUT/'scene_source.json').read_text())
    if len(source['frames'])==192:
        (OUT/'pan_scene_source.json').write_text(json.dumps(source,indent=2))
        original=json.loads((HERE/'intro_atmosphere/scene_source.json').read_text())
        source['frames']=[f for f in original['frames'] if f['shot']!='drone']+source['frames']
        source['shots']=[['ceiling',6],['rubble',6],['drone',8]]
        source['reused_shots_source']=str(HERE/'intro_atmosphere/scene_source.json')
        source['camera_revision']='Fixed-position slow angular pan from drone to blue-clothed survivor, with focus pull'
        (OUT/'scene_source.json').write_text(json.dumps(source,indent=2))
    base.render()
    meta=json.loads((OUT/'source_evidence.json').read_text(encoding='utf8'))
    meta.update(revision='Corrected opening pronunciation and slow survivor reveal',opening_audio_check=str(OUT/'independent_transcription.json'))
    (OUT/'source_evidence.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')

def preview():base.preview()
if __name__=='__main__':globals()[sys.argv[1]]()
