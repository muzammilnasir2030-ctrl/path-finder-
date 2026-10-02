import pygame, math, random, time, sys, heapq
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

WIN_W,WIN_H,PANEL_W,ROWS,COLS,CS = 1200,750,280,12,15,2.0
def rgb(r,g,b): return r/255,g/255,b/255
C_BG=(8,11,18); C_PANEL=(13,17,32); C_ACC=(74,242,184); C_TXT=(200,210,230)
C_DIM=(80,95,120); C_BTN=(22,28,48); C_BTH=(30,40,65); C_BTA=(20,55,50); C_BRD=(35,45,70)
C_ROAD=rgb(22,26,38); C_PATH=rgb(55,220,160)
C_REST=rgb(40,160,90); C_CUST=rgb(200,55,80); C_RIDER=rgb(74,242,184)
pygame.init()
FT=pygame.font.SysFont("Consolas",26,bold=True)
FM=pygame.font.SysFont("Consolas",17,bold=True)
FS=pygame.font.SysFont("Consolas",13)

# ── Game ──────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.start,self.goal=(2,2),(12,9); self.generate()
    def generate(self):
        self.grid=[[1]*COLS for _ in range(ROWS)]
        for y in range(ROWS):
            for x in range(COLS):
                if x%4==0 or y%3==0 or random.random()<.35: self.grid[y][x]=0
        sx,sy=self.start; gx,gy=self.goal
        for x in range(sx,gx+1): self.grid[sy][x]=0
        for y in range(sy,gy+1): self.grid[y][gx]=0
        for _ in range(12):
            bx,by=random.randint(1,COLS-2),random.randint(1,ROWS-2)
            if (bx,by) not in (self.start,self.goal): self.grid[by][bx]=1
        self.grid[sy][sx]=self.grid[gy][gx]=0
        self.bld={(x,y):.6+random.random()*3.2 for y in range(ROWS) for x in range(COLS) if self.grid[y][x]}
    def nb(self,p):
        x,y=p
        return [(x+dx,y+dy) for dx,dy in[(0,1),(1,0),(0,-1),(-1,0)]
                if 0<=x+dx<COLS and 0<=y+dy<ROWS and self.grid[y+dy][x+dx]==0]
    def astar(self):
        h=lambda a,b:abs(a[0]-b[0])+abs(a[1]-b[1])
        heap=[(0,self.start)]; came={self.start:None}; g={self.start:0}; vis=set(); t0=time.time()
        while heap:
            _,cur=heapq.heappop(heap)
            if cur in vis: continue
            vis.add(cur)
            if cur==self.goal:
                p=[]; c=cur
                while c: p.append(c); c=came[c]
                return p[::-1],vis,(time.time()-t0)*1000
            for n in self.nb(cur):
                tg=g[cur]+1
                if tg<g.get(n,1e9): came[n]=cur; g[n]=tg; heapq.heappush(heap,(tg+h(n,self.goal),n))
        return [],vis,(time.time()-t0)*1000

# ── Camera ────────────────────────────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.tgt=[(COLS-1)*CS/2,0,(ROWS-1)*CS/2]; self.th,self.ph,self.r=.55,.78,52.
        self.px=self.pz=0.; self.drag=self.rd=False; self.last=(0,0)
    def apply(self):
        st,ct,sp,cp=math.sin(self.th),math.cos(self.th),math.sin(self.ph),math.cos(self.ph)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        gluLookAt(self.tgt[0]+self.px+self.r*st*sp, self.r*cp, self.tgt[2]+self.pz+self.r*ct*sp,
                  self.tgt[0]+self.px, 0, self.tgt[2]+self.pz, 0,1,0)
    def on_event(self,e):
        if e.type==MOUSEBUTTONDOWN and e.pos[0]>PANEL_W:
            if e.button==1: self.drag=True; self.last=e.pos
            if e.button==3: self.rd=True;   self.last=e.pos
            if e.button==4: self.r=max(12,self.r-2.5)
            if e.button==5: self.r=min(90,self.r+2.5)
        if e.type==MOUSEBUTTONUP:
            if e.button==1: self.drag=False
            if e.button==3: self.rd=False
        if e.type==MOUSEMOTION:
            dx=(e.pos[0]-self.last[0])*.012; dy=(e.pos[1]-self.last[1])*.012; self.last=e.pos
            if self.drag: self.th-=dx; self.ph=max(.15,min(1.35,self.ph+dy))
            if self.rd:   self.px-=dx*3; self.pz+=dy*3

# ── 3-D primitives ────────────────────────────────────────────────────────────
def box(cx,cy,cz,w,h,d,col,alpha=1.):
    r,g,b=col; x0,x1=cx-w/2,cx+w/2; z0,z1=cz-d/2,cz+d/2; y1=cy+h
    glBegin(GL_QUADS)
    for fr,fg,fb,vs in[
        (min(1,r+.12),min(1,g+.12),min(1,b+.12),[(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)]),
        (r*.85,g*.85,b*.85,[(x0,cy,z1),(x1,cy,z1),(x1,y1,z1),(x0,y1,z1)]),
        (r*.75,g*.75,b*.75,[(x1,cy,z0),(x0,cy,z0),(x0,y1,z0),(x1,y1,z0)]),
        (r*.8, g*.8, b*.8, [(x0,cy,z0),(x0,cy,z1),(x0,y1,z1),(x0,y1,z0)]),
        (r*.8, g*.8, b*.8, [(x1,cy,z1),(x1,cy,z0),(x1,y1,z0),(x1,y1,z1)]),
        (r*.5, g*.5, b*.5, [(x0,cy,z1),(x0,cy,z0),(x1,cy,z0),(x1,cy,z1)])]:
        glColor4f(fr,fg,fb,alpha)
        for v in vs: glVertex3f(*v)
    glEnd()

def cyl(cx,cy,cz,rad,h,col,sg=16):
    glColor3f(*col)
    for yo,s in[(h,1),(0,-1)]:
        glBegin(GL_TRIANGLE_FAN); glVertex3f(cx,cy+yo,cz)
        for i in range(sg+1): a=s*2*math.pi*i/sg; glVertex3f(cx+rad*math.cos(a),cy+yo,cz+rad*math.sin(a))
        glEnd()
    glBegin(GL_QUAD_STRIP)
    for i in range(sg+1):
        a=2*math.pi*i/sg; glVertex3f(cx+rad*math.cos(a),cy,cz+rad*math.sin(a)); glVertex3f(cx+rad*math.cos(a),cy+h,cz+rad*math.sin(a))
    glEnd()

def torus(R,r,col,mj=28,mn=10):
    for i in range(mj):
        glBegin(GL_QUAD_STRIP)
        for j in range(mn+1):
            for di in[0,1]:
                ph=2*math.pi*(i+di)/mj; th=2*math.pi*j/mn
                glColor3f(*col); glVertex3f((R+r*math.cos(th))*math.cos(ph),r*math.sin(th),(R+r*math.cos(th))*math.sin(ph))
        glEnd()

def sph(cx,cy,cz,rad,col,sk=10,sl=12):
    r,g,b=col
    for i in range(sk):
        la0=math.pi*(-.5+i/sk); la1=math.pi*(-.5+(i+1)/sk)
        z0,zr0=math.sin(la0),math.cos(la0); z1,zr1=math.sin(la1),math.cos(la1)
        glBegin(GL_QUAD_STRIP)
        for j in range(sl+1):
            lg=2*math.pi*j/sl; x,y=math.cos(lg),math.sin(lg)
            glColor3f(r*.85,g*.85,b*.85); glVertex3f(cx+x*zr0*rad,cy+z0*rad,cz+y*zr0*rad)
            glColor3f(r,g,b);             glVertex3f(cx+x*zr1*rad,cy+z1*rad,cz+y*zr1*rad)
        glEnd()

# ── Scene ─────────────────────────────────────────────────────────────────────
def draw_scene(game,vis,path,rpos,rang,t):
    glColor3f(.04,.05,.09); glBegin(GL_QUADS)
    for v in[(-4,-.05,-4),(COLS*CS+4,-.05,-4),(COLS*CS+4,-.05,ROWS*CS+4),(-4,-.05,ROWS*CS+4)]: glVertex3f(*v)
    glEnd()
    ps=set(path)
    for y in range(ROWS):
        for x in range(COLS):
            wx,wz=x*CS,y*CS; is_s=(x,y)==game.start; is_g=(x,y)==game.goal
            if game.grid[y][x]==0:
                box(wx,0,wz,CS-.06,.1,CS-.06,C_ROAD)
                if (x,y) in vis and not is_s and not is_g:
                    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
                    box(wx,.1,wz,CS*.88,.06,CS*.88,(.06,.22,.40),alpha=.85); glDisable(GL_BLEND)
                if (x,y) in ps and not is_s and not is_g: box(wx,.12,wz,CS*.55,.09,CS*.55,C_PATH)
                for pos,col,spd in[(game.start,C_REST,70),(game.goal,C_CUST,-60)]:
                    if (x,y)==pos:
                        box(wx,.1,wz,CS*.88,.08,CS*.88,col); cyl(wx,.2,wz,.08,1.1,col)
                        glPushMatrix(); glTranslatef(wx,.22,wz); glRotatef(t*spd%360,0,1,0); torus(.65,.08,col); glPopMatrix()
            else:
                h=game.bld.get((x,y),1.5); s=.28+(h/5)*.45
                wb=CS*(.64+hash((x,y,0))%100/500); db=CS*(.64+hash((x,y,1))%100/500)
                box(wx,0,wz,wb,h,db,(.13+s*.1,.14+s*.08,.22+s*.12))
                if h>1.4:
                    for wr in range(min(int(h/.65),5)):
                        if hash((x,y,wr))%3!=0:
                            box(wx+wb/2+.02,.3+wr*.62,wz,.04,.20,.18,((.9,.8,.4) if hash((x,y,wr))%4==0 else (.4,.7,1.)))
    if len(path)>1:
        glLineWidth(4); glColor3f(*C_PATH); glBegin(GL_LINE_STRIP)
        for p in path: glVertex3f(p[0]*CS,.30,p[1]*CS)
        glEnd(); glLineWidth(1)
    if rpos:
        glPushMatrix(); glTranslatef(*rpos); glRotatef(rang,0,1,0)
        box(0,.28,0,.72,.24,.28,rgb(220,228,240)); cyl(-.28,.05,0,.18,.12,rgb(25,28,38),sg=14); cyl(.28,.05,0,.18,.12,rgb(25,28,38),sg=14)
        box(-.04,.60,0,.22,.38,.20,C_RIDER); sph(-.04,1.08,0,.17,(.22,.82,.60)); box(.22,.54,0,.30,.28,.26,rgb(242,201,74))
        glPopMatrix()

# ── 2-D UI ────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self,x,y,w,h,lbl): self.r=pygame.Rect(x,y,w,h); self.lbl=lbl; self.active=False
    def draw(self,s,m):
        c=C_BTA if self.active else(C_BTH if self.r.collidepoint(m) else C_BTN)
        bd=C_ACC if(self.active or self.r.collidepoint(m)) else C_BRD
        pygame.draw.rect(s,c,self.r,border_radius=5); pygame.draw.rect(s,bd,self.r,2,border_radius=5)
        if self.active: pygame.draw.rect(s,C_ACC,(self.r.x,self.r.y,3,self.r.h),border_radius=3)
        t=FM.render(self.lbl,True,C_TXT); s.blit(t,(self.r.centerx-t.get_width()//2,self.r.centery-t.get_height()//2))
    def hit(self,p): return self.r.collidepoint(p)

class Slider:
    def __init__(self,x,y,w,lo,hi,v): self.x,self.y,self.w,self.lo,self.hi,self.val,self.drag=x,y,w,lo,hi,v,False
    def draw(self,s):
        s.blit(FS.render(f"SPEED: {self.val}",True,C_DIM),(self.x,self.y))
        by=self.y+22; f=(self.val-self.lo)/(self.hi-self.lo)
        pygame.draw.rect(s,C_BRD,(self.x,by,self.w,4),border_radius=2)
        pygame.draw.rect(s,C_ACC,(self.x,by,int(f*self.w),4),border_radius=2)
        pygame.draw.circle(s,C_ACC,(int(self.x+f*self.w),by+2),7)
    def on_event(self,e):
        by=self.y+22
        if e.type==MOUSEBUTTONDOWN and e.button==1 and abs(e.pos[1]-by)<10 and self.x<=e.pos[0]<=self.x+self.w: self.drag=True
        if e.type==MOUSEBUTTONUP and e.button==1: self.drag=False
        if e.type==MOUSEMOTION and self.drag: self.val=int(self.lo+max(0,min(1,(e.pos[0]-self.x)/self.w))*(self.hi-self.lo))

def draw_panel(surf,stats,bp,br,bn,sl,mouse):
    surf.fill(C_PANEL); pygame.draw.rect(surf,C_ACC,(0,0,PANEL_W,3))
    surf.blit(FT.render("Food rider sim",True,C_ACC),(18,14)); surf.blit(FT.render("PATHFINDER",True,C_TXT),(18,42))
    surf.blit(FS.render("// A* DELIVERY SYSTEM",True,C_DIM),(18,70))
    pygame.draw.line(surf,C_BRD,(14,90),(PANEL_W-14,90),1)
    surf.blit(FS.render("// FIND PATH",True,C_DIM),(18,98)); bp.draw(surf,mouse)
    surf.blit(FS.render("// CONTROLS",True,C_DIM),(18,182)); br.draw(surf,mouse); bn.draw(surf,mouse)
    pygame.draw.line(surf,C_BRD,(14,258),(PANEL_W-14,258),1)
    surf.blit(FS.render("// STATISTICS",True,C_DIM),(18,266))
    for i,(k,v) in enumerate([("ALGORITHM","A*"),("EXPLORED",str(stats["explored"])),
                               ("PATH LEN",str(stats["path_len"])),("TIME",f"{stats['time_ms']} ms")]):
        surf.blit(FS.render(k,True,C_DIM),(20,288+i*34))
        vt=FM.render(v,True,C_ACC); surf.blit(vt,(PANEL_W-vt.get_width()-14,286+i*34))
        pygame.draw.line(surf,C_BRD,(14,314+i*34),(PANEL_W-14,314+i*34),1)
    pygame.draw.line(surf,C_BRD,(14,426),(PANEL_W-14,426),1)
    surf.blit(FS.render("// SPEED",True,C_DIM),(18,434)); sl.draw(surf)
    pygame.draw.line(surf,C_BRD,(14,500),(PANEL_W-14,500),1)
    surf.blit(FS.render("// LEGEND",True,C_DIM),(18,508))
    for i,(c,n) in enumerate([(C_REST,"Restaurant"),(C_CUST,"Customer"),((14,50,90),"Explored"),(C_PATH,"Final Path"),(C_RIDER,"Rider")]):
        pygame.draw.rect(surf,c,(18,528+i*22,12,12),border_radius=2); surf.blit(FS.render(n,True,C_TXT),(36,526+i*22))
    surf.blit(FS.render("DRAG orbit|RMB pan|SCROLL zoom",True,C_DIM),(10,WIN_H-22))
    pygame.draw.line(surf,C_BRD,(PANEL_W-1,0),(PANEL_W-1,WIN_H),1)

def to_tex(surf,tid=None):
    d=pygame.image.tostring(surf,"RGBA",True); w,h=surf.get_size()
    tid=tid or glGenTextures(1); glBindTexture(GL_TEXTURE_2D,tid)
    glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,d)
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR); glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
    return tid

def blit(tid,x,y,w,h):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); glOrtho(0,WIN_W,WIN_H,0,-1,1)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D,tid)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA); glColor4f(1,1,1,1)
    glBegin(GL_QUADS)
    glTexCoord2f(0,1); glVertex2f(x,y); glTexCoord2f(1,1); glVertex2f(x+w,y)
    glTexCoord2f(1,0); glVertex2f(x+w,y+h); glTexCoord2f(0,0); glVertex2f(x,y+h)
    glEnd(); glDisable(GL_TEXTURE_2D); glDisable(GL_BLEND)
    glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()

class StatusBar:
    def __init__(self): self.msg=""; self.alpha=0; self.t=0
    def show(self,m): self.msg=m; self.alpha=255; self.t=time.time()
    def update(self):
        if time.time()-self.t>2.2 and self.alpha>0: self.alpha=max(0,self.alpha-8)
    def draw(self,s):
        if not self.alpha: return
        txt=FM.render(self.msg,True,C_ACC); w,h=txt.get_size(); x=PANEL_W+(WIN_W-PANEL_W-w)//2; y=WIN_H-48
        bg=pygame.Surface((w+30,h+14),pygame.SRCALPHA); bg.fill((8,11,18,int(self.alpha*.88))); s.blit(bg,(x-15,y-7))
        pygame.draw.rect(s,(*C_ACC,self.alpha),(x-15,y-7,w+30,h+14),1,border_radius=3)
        txt.set_alpha(self.alpha); s.blit(txt,(x,y))

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    pygame.display.set_mode((WIN_W,WIN_H),DOUBLEBUF|OPENGL|RESIZABLE)
    pygame.display.set_caption("Food rider simulator Pathfinder 3D — A*")
    glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    def vp():
        glViewport(PANEL_W,0,WIN_W-PANEL_W,WIN_H); glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(45,(WIN_W-PANEL_W)/WIN_H,.1,200)
    vp(); cam=Camera(); game=Game()
    bp=Button(14,114,PANEL_W-28,52,"  FIND BEST PATH  (A*)")
    br=Button(14,198,(PANEL_W-34)//2,46,"  RESET")
    bn=Button(14+(PANEL_W-34)//2+6,198,(PANEL_W-34)//2,46,"  NEW MAP")
    sl=Slider(18,448,PANEL_W-36,1,10,5)
    stats={"explored":0,"path_len":0,"time_ms":"0.00"}
    path=[]; vis=set(); anim=False; ri=0; rpos=None; rang=0.; la=0.
    ps=pygame.Surface((PANEL_W,WIN_H),pygame.SRCALPHA); os_=pygame.Surface((WIN_W,WIN_H),pygame.SRCALPHA)
    pt=None; sb=StatusBar(); sb.show("CITY LOADED — CLICK FIND BEST PATH")
    clock=pygame.time.Clock(); t0=time.time()

    def run():
        nonlocal path,vis,anim,ri,rpos,la
        path,vis,ms=game.astar(); stats.update({"explored":len(vis),"path_len":len(path),"time_ms":f"{ms:.2f}"})
        bp.active=True
        if not path: sb.show("NO PATH FOUND"); return
        anim=True; ri=0; la=time.time(); sb.show(f"A* — {len(path)} STEPS | {len(vis)} EXPLORED")

    def reset():
        nonlocal path,vis,anim,rpos
        path=[]; vis=set(); anim=False; rpos=None; bp.active=False
        stats.update({"explored":0,"path_len":0,"time_ms":"0.00"}); sb.show("RESET")

    running=True
    while running:
        t=time.time()-t0; m=pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type==QUIT or(e.type==KEYDOWN and e.key==K_ESCAPE): running=False
            cam.on_event(e); sl.on_event(e)
            if e.type==MOUSEBUTTONDOWN and e.button==1 and e.pos[0]<PANEL_W:
                if bp.hit(e.pos) and not anim: run()
                if br.hit(e.pos): reset()
                if bn.hit(e.pos): reset(); game.__init__(); sb.show("NEW CITY MAP GENERATED")
        if anim and path:
            if time.time()-la>.22-sl.val*.019: ri=min(ri+1,len(path)-1); la=time.time()
            cur=path[ri]; rpos=(cur[0]*CS,.1,cur[1]*CS)
            if ri>0:
                pv=path[ri-1]; dx=cur[0]-pv[0]; dz=cur[1]-pv[1]
                if dx or dz: rang=math.degrees(math.atan2(dx,dz))
            if ri==len(path)-1: anim=False; sb.show("DELIVERY COMPLETE!")
        vp(); glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT); glClearColor(*[c/255 for c in C_BG],1.); cam.apply()
        draw_scene(game,vis,path,rpos,rang,t)
        draw_panel(ps,stats,bp,br,bn,sl,m); pt=to_tex(ps,pt)
        glViewport(0,0,WIN_W,WIN_H); glDisable(GL_DEPTH_TEST); blit(pt,0,0,PANEL_W,WIN_H); glEnable(GL_DEPTH_TEST)
        sb.update(); os_.fill((0,0,0,0)); sb.draw(os_)
        glViewport(0,0,WIN_W,WIN_H); glDisable(GL_DEPTH_TEST); ov=to_tex(os_); blit(ov,0,0,WIN_W,WIN_H)
        glDeleteTextures([ov]); glEnable(GL_DEPTH_TEST)
        pygame.display.flip(); clock.tick(60)
    pygame.quit(); sys.exit()

if __name__=="__main__": main()