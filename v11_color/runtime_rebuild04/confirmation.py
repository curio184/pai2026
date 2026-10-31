class VisualConfirmation:
    """Three distinct recent model input images; no target locations."""
    def __init__(self, color):
        self.color=color
        self.hits=[]
        self.last_id=None
        self.last_seen=None

    def update(self, packet, now):
        if packet is None or now-packet['sim_time_capture']>2.5:
            return False
        if packet['id'] != self.last_id:
            self.last_id=packet['id']
            candidates=[p for p in packet.get('perception',{}).get('persons',[]) if p['clothing_color']==self.color]
            if len(candidates)==1:
                current=candidates[0]
                if self.hits:
                    a=self.hits[-1]['person']['bbox']; b=current['bbox']
                    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
                    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
                    if intersection/max(union,1)<.20:
                        self.hits=[]
                self.last_seen=packet['sim_time_capture']
                self.hits.append(dict(id=packet['id'],t=packet['sim_time_capture'], image_file=packet['image_file'],
                                      image_sha256=packet['image_sha256'],person=current))
            else:
                self.hits=[]
        self.hits=[h for h in self.hits if now-h['t']<=5]
        return len(self.hits)>=3 and self.hits[-1]['t']-self.hits[-3]['t']>=.4
