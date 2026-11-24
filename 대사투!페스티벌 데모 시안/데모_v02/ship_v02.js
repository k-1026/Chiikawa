/* 외지몽 우주선: 하늘을 랜덤한 곡선으로 날아다니며 뒤로 불꽃 + 연기를 내뿜는다 */
(function(){
  var hero=document.querySelector('.hero'), ship=document.querySelector('.ship'), cv=document.getElementById('exhaust');
  if(!hero||!ship||!cv) return;
  var ctx=cv.getContext('2d'), W=0,H=0,dpr=1;
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function size(){
    dpr=Math.min(window.devicePixelRatio||1,2);
    W=hero.clientWidth; H=hero.clientHeight;
    cv.width=W*dpr; cv.height=H*dpr; ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  size(); window.addEventListener('resize',size);
  if(reduce){ ship.style.transform='translate('+(W*.7)+'px,40px)'; return; }

  function rnd(a,b){return a+Math.random()*(b-a)}
  var path=[], total=0, dist=0, wait=0.8, flying=false, flip=1, last=0;
  var parts=[];

  /* 랜덤 경로: 화면 밖에서 시작 -> 곡선으로 가로질러 -> 반대편 밖으로 */
  function makePath(){
    var sw=ship.offsetWidth||100, dirR=Math.random()<.5, n=Math.round(rnd(4,6));
    var x0=dirR?-sw*1.5:W+sw*.5, x1=dirR?W+sw*.5:-sw*1.5;
    var pts=[], top=H*.06, bot=Math.min(H*.62,H-sw*1.6);
    for(var i=0;i<n;i++){
      var t=i/(n-1);
      pts.push([x0+(x1-x0)*t+(i>0&&i<n-1?rnd(-W*.05,W*.05):0), rnd(top,bot)]);
    }
    pts.unshift([pts[0][0]+(dirR?-60:60),pts[0][1]]); pts.push([pts[pts.length-1][0]+(dirR?60:-60),pts[pts.length-1][1]]);
    /* Catmull-Rom 샘플링 */
    var out=[];
    for(var s=0;s<pts.length-3;s++){
      var p0=pts[s],p1=pts[s+1],p2=pts[s+2],p3=pts[s+3];
      for(var k=0;k<24;k++){
        var u=k/24,u2=u*u,u3=u2*u;
        out.push([
          .5*((2*p1[0])+(-p0[0]+p2[0])*u+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*u2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*u3),
          .5*((2*p1[1])+(-p0[1]+p2[1])*u+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*u2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*u3)
        ]);
      }
    }
    path=out; total=0;
    for(var j=0;j<path.length;j++){ path[j].push(total); if(j<path.length-1){var dx=path[j+1][0]-path[j][0],dy=path[j+1][1]-path[j][1];total+=Math.sqrt(dx*dx+dy*dy);} }
    dist=0; flying=true; flip=dirR?-1:1;   /* 그림은 왼쪽을 보고 있음: 오른쪽으로 가면 좌우반전 */
  }
  function posAt(d){
    var lo=0,hi=path.length-1;
    while(hi-lo>1){var m=(lo+hi)>>1; if(path[m][2]<=d) lo=m; else hi=m;}
    var a=path[lo],b=path[hi],seg=(b[2]-a[2])||1,t=Math.min(1,Math.max(0,(d-a[2])/seg));
    return {x:a[0]+(b[0]-a[0])*t,y:a[1]+(b[1]-a[1])*t,vx:b[0]-a[0],vy:b[1]-a[1]};
  }

  function emit(x,y,vx,vy,sw,dt){
    var L=Math.sqrt(vx*vx+vy*vy)||1, bx=-vx/L, by=-vy/L;           /* 진행 반대 방향 */
    var n=Math.max(1,Math.round(dt*90));
    for(var i=0;i<n;i++){
      /* 불꽃: 짧고 밝게 */
      if(Math.random()<.6) parts.push({t:'f',x:x+rnd(-2,2),y:y+rnd(-2,2),vx:bx*rnd(45,90)+rnd(-10,10),vy:by*rnd(45,90)+rnd(-10,10),life:rnd(.14,.28),age:0,r0:sw*rnd(.05,.085),r1:sw*.02});
      /* 연기: 길게 퍼지며 사라짐 */
      if(Math.random()<.55) parts.push({t:'s',x:x+bx*sw*.1+rnd(-3,3),y:y+by*sw*.1+rnd(-3,3),vx:bx*rnd(14,40)+rnd(-10,10),vy:by*rnd(14,40)+rnd(-18,-4),life:rnd(1.3,2.1),age:0,r0:sw*rnd(.1,.16),r1:sw*rnd(.45,.75),sh:Math.round(rnd(222,246))});
    }
  }

  function draw(dt){
    ctx.clearRect(0,0,W,H);
    var i,p,k,r,a,g;
    /* 연기 먼저 */
    for(i=0;i<parts.length;i++){ p=parts[i]; if(p.t!=='s') continue;
      k=p.age/p.life; r=p.r0+(p.r1-p.r0)*k; a=(1-k)*(1-k)*.5;
      g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r);
      g.addColorStop(0,'rgba('+p.sh+','+(p.sh-16)+','+(p.sh-42)+','+a+')'); g.addColorStop(1,'rgba('+p.sh+','+(p.sh-16)+','+(p.sh-42)+',0)');
      ctx.fillStyle=g; ctx.beginPath(); ctx.arc(p.x,p.y,r,0,6.2832); ctx.fill();
    }
    /* 불꽃은 위에 */
    for(i=0;i<parts.length;i++){ p=parts[i]; if(p.t!=='f') continue;
      k=p.age/p.life; r=p.r0+(p.r1-p.r0)*k; a=1-k;
      g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r*1.6);
      g.addColorStop(0,'rgba(255,255,235,'+a+')'); g.addColorStop(.35,'rgba(255,214,102,'+a*.95+')'); g.addColorStop(.7,'rgba(255,128,48,'+a*.6+')'); g.addColorStop(1,'rgba(255,90,30,0)');
      ctx.fillStyle=g; ctx.beginPath(); ctx.arc(p.x,p.y,r*1.6,0,6.2832); ctx.fill();
    }
  }

  function frame(ts){
    var dt=Math.min(.05,(ts-last)/1000||.016); last=ts;
    var sw=ship.offsetWidth||100;
    if(!flying){ wait-=dt; ship.style.opacity=0; if(wait<=0) makePath(); }
    else{
      dist+=dt*Math.max(110,W*.11);
      if(dist>=total){ flying=false; wait=rnd(1.2,3.5); ship.style.opacity=0; }
      else{
        var q=posAt(dist), sh=ship.offsetHeight||96;
        var rot=Math.max(-12,Math.min(12,flip*-Math.atan(q.vy/(Math.abs(q.vx)||1))*180/Math.PI*.4));
        ship.style.opacity=1;
        ship.style.transform='translate('+(q.x-sw/2)+'px,'+(q.y-sh/2)+'px) rotate('+rot+'deg) scaleX('+flip+')';
        /* 추진기는 그림 오른쪽(왼쪽 보며 날 때 꼬리) */
        var tx=q.x+flip*sw*.42, ty=q.y-sh*.12;
        emit(tx,ty,q.vx,q.vy,sw,dt);
      }
    }
    for(var i=parts.length-1;i>=0;i--){ var p=parts[i]; p.age+=dt; if(p.age>=p.life){parts.splice(i,1);continue;} p.x+=p.vx*dt; p.y+=p.vy*dt; p.vx*=.985; }
    draw(dt);
    requestAnimationFrame(frame);
  }
  ship.style.opacity=0; requestAnimationFrame(frame);
})();
