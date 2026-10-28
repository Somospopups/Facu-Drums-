from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import io,json,base64,struct,traceback,os
import numpy as np
import soundfile as sf
import librosa

ROOT=Path(__file__).parent

# Superior Drummer 3: default mapping for the supported articulations.
SD3_MAP = {'kick': 36, 'snare_center': 38, 'hihat_closed': 42}

def vlq(v):
    b=[v & 127]; v >>= 7
    while v: b.insert(0,(v & 127)|128); v >>= 7
    return bytes(b)

def midi_file(hits,bpm):
    tempo=round(60000000/bpm)
    ev=[(0, b'\xff\x51\x03'+tempo.to_bytes(3,'big'))]
    for h in hits:
        t=round(h['time']*bpm/60*480)
        ev.extend([(t,bytes([0x99,h['note'],h['velocity']])),(t+60,bytes([0x89,h['note'],0]))])
    track=b''; prev=0
    for t,msg in sorted(ev,key=lambda x:x[0]):
        track+=vlq(t-prev)+msg;prev=t
    track+=b'\x00\xff\x2f\x00'
    return b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(track))+track

def analyze(raw,sensitivity,quantize,manual_bpm):
    y,sr=sf.read(io.BytesIO(raw),dtype='float32',always_2d=True)
    if len(y)/sr>180: raise ValueError('El audio debe durar como máximo 3 minutos.')
    y=y.mean(axis=1)
    if len(y)<sr*.2 or np.max(np.abs(y))<1e-5: raise ValueError('El audio está vacío, es muy corto o no tiene señal audible.')
    y=librosa.resample(y,orig_sr=sr,target_sr=22050); sr=22050; hop=256
    spec=np.abs(librosa.stft(y,n_fft=1024,hop_length=hop))
    freq=librosa.fft_frequencies(sr=sr,n_fft=1024)
    ranges=[(35,180,SD3_MAP['kick'],'Bombo'),(180,3000,SD3_MAP['snare_center'],'Caja'),(5000,10500,SD3_MAP['hihat_closed'],'Hi-hat')]
    env=librosa.onset.onset_strength(S=librosa.amplitude_to_db(spec,ref=np.max),sr=sr,hop_length=hop)
    est,_=librosa.beat.beat_track(onset_envelope=env,sr=sr,hop_length=hop)
    bpm=float(manual_bpm) if manual_bpm else float(np.asarray(est).reshape(-1)[0])
    if not np.isfinite(bpm) or bpm<=0: bpm=120.
    hits=[]
    for lo,hi,note,label in ranges:
        band=spec[(freq>=lo)&(freq<hi)]
        energy=np.sqrt(np.mean(band**2,axis=0))
        flux=np.maximum(0,np.diff(energy,prepend=energy[0]))
        if flux.max()<=1e-9: continue
        flux=flux/flux.max()
        frames=librosa.onset.onset_detect(onset_envelope=flux,sr=sr,hop_length=hop,backtrack=False,delta=.24-.0017*sensitivity,wait=5,pre_max=3,post_max=3,pre_avg=8,post_avg=8,units='frames')
        for f in frames:
            t=max(0,float(librosa.frames_to_time(f,sr=sr,hop_length=hop))-.015)
            if quantize: t=round(t/(60/bpm/4))*(60/bpm/4)
            strength=float(flux[f]); velocity=int(np.clip(40+87*np.sqrt(strength),1,127))
            hits.append({'time':round(t,4),'note':note,'label':label,'velocity':velocity})
    hits.sort(key=lambda h:h['time'])
    return {'mapping':'Superior Drummer 3 — Default (36/38/42)','bpm':round(bpm,1),'duration':round(len(y)/sr,2),'hits':hits,'midi':base64.b64encode(midi_file(hits,bpm)).decode()}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] not in ['/', '/index.html']:
            self.send_error(404);return
        data=(ROOT/'index.html').read_bytes()
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
    def do_POST(self):
        if self.path!='/api/transcribe': self.send_error(404);return
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<=45*1024*1024: raise ValueError('El archivo debe pesar menos de 45 MB.')
            raw=self.rfile.read(size)
            sensitivity=float(self.headers.get('X-Sensitivity','55'))
            bpm=float(self.headers.get('X-Bpm','0'))
            if bpm and not 30<=bpm<=300: raise ValueError('El tempo debe estar entre 30 y 300 BPM.')
            result=analyze(raw,np.clip(sensitivity,0,100),self.headers.get('X-Quantize')=='true',bpm)
            code=200
        except Exception as e:
            traceback.print_exc()
            result={'error': str(e) if isinstance(e,ValueError) else 'No se pudo leer o analizar el audio. Probá con WAV, FLAC u OGG.'};code=400
        data=json.dumps(result).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)

if __name__=='__main__':
    port=int(os.environ.get('PORT','8000'))
    print(f'Drumline disponible en el puerto {port}',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
