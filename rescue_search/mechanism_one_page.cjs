// Editable SVG diagram for the existing local video; original CG asset retained.
const fs=require('fs'),path=require('path');
const root=process.env.RESCUE_PROJECT_ROOT;
const out=path.join(root,'output/video/mechanism_review');fs.mkdirSync(out,{recursive:true});
const asset=fs.readFileSync(path.join(root,'tmp/premium/opening/0060.jpg')).toString('base64');
const bg='#081219',fg='#f4f4ee',muted='#b6c5cb',cyan='#76d1ce',gold='#e9c78e';
const text=(x,y,s,size=30,color=fg,weight=500,anchor='start')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}" text-anchor="${anchor}">${s}</text>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1920" height="1080" viewBox="0 0 1920 1080">
<metadata>Unified conceptual architecture. Wireless links and real StampFly integration are the proposed hardware configuration; evaluated flights use the simulation. SmolVLA motion generation operates within mission-control software.</metadata>
<defs>
 <marker id="cyan" markerUnits="userSpaceOnUse" markerWidth="19" markerHeight="18" refX="17" refY="9" orient="auto"><path d="M0 0L18 9L0 18Z" fill="${cyan}"/></marker>
 <marker id="gold" markerUnits="userSpaceOnUse" markerWidth="19" markerHeight="18" refX="17" refY="9" orient="auto"><path d="M0 0L18 9L0 18Z" fill="${gold}"/></marker>
 <linearGradient id="fadeLeft"><stop offset="0" stop-color="white" stop-opacity="0"/><stop offset=".1" stop-color="white"/><stop offset=".9" stop-color="white"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient>
 <linearGradient id="fadeVertical" x2="0" y2="1"><stop offset="0" stop-color="white" stop-opacity="0"/><stop offset=".12" stop-color="white"/><stop offset=".85" stop-color="white"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient>
 <mask id="imageMask"><rect x="95" y="390" width="550" height="420" fill="url(#fadeVertical)"/></mask>
</defs>
<style>text {font-family:'Yu Gothic','Yu Gothic UI',sans-serif} .en {font-family:Bahnschrift,'Yu Gothic',sans-serif}</style>
<rect width="1920" height="1080" fill="${bg}"/>
<path d="M65 70V177" stroke="${gold}" stroke-width="5"/>
${text(96,100,'しくみ',29,gold,600)}
${text(96,175,'言葉と映像から、飛行動作を生成',56,fg,700)}

<!-- Language enters the same controller receiving the visual observations. -->
${text(1465,258,'「青い服の人を探して」',36,fg,600,'middle')}
<path d="M1465 285V339" fill="none" stroke="${muted}" stroke-width="2" marker-end="url(#cyan)"/>

<!-- Physical robot, kept as the familiar original CG, with no invented illustration. -->
${text(96,357,'ドローン',37,fg,700)}
${text(328,357,'StampFly',32,gold,500)}
<g mask="url(#imageMask)"><svg x="95" y="390" width="550" height="420" viewBox="620 155 1080 845" preserveAspectRatio="xMidYMid meet"><image width="1920" height="1080" xlink:href="data:image/jpeg;base64,${asset}"/></svg></g>
${text(365,869,'機体側で姿勢を安定化',28,muted,500,'middle')}

<!-- The upper and lower lanes form the large, readable wireless feedback loop. -->
${text(875,445,'映像を送る',34,cyan,700,'middle')}
<path d="M650 485H1106" stroke="${cyan}" stroke-width="4" fill="none" marker-end="url(#cyan)"/>
${text(875,536,'カメラ映像・機体の状態',25,muted,500,'middle')}
${text(875,653,'無線通信',25,muted,500,'middle')}
${text(875,763,'飛行指令を返す',34,gold,700,'middle')}
<path d="M1110 805H650" stroke="${gold}" stroke-width="4" fill="none" marker-end="url(#gold)"/>
${text(875,856,'移動・旋回・離着陸',25,muted,500,'middle')}

<!-- One physical PC contains one controller and the VLA it calls. -->
<rect x="1110" y="355" width="714" height="550" rx="12" fill="#101e27" stroke="#42545d" stroke-width="1.4"/>
${text(1148,402,'制御用PC',35,fg,700)}
${text(1148,451,'制御プログラム',27,muted,600)}
${text(1148,488,'捜索の進行管理・映像の受信・指令の送信',24,muted,500)}
<path d="M1465 506V539" stroke="${cyan}" stroke-width="3" fill="none" marker-end="url(#cyan)"/>
<rect x="1190" y="551" width="554" height="192" rx="6" fill="#0a1922" stroke="${cyan}" stroke-width="1.4"/>
${text(1467,603,'SmolVLA',46,fg,600,'middle')}
${text(1467,652,'映像・指示・機体の状態から',26,muted,500,'middle')}
${text(1467,703,'次の飛行動作を生成',32,fg,700,'middle')}
<path d="M1465 748V805H1110" stroke="${gold}" stroke-width="3" fill="none"/>
${text(1465,856,'生成した動作を飛行指令に変換',26,muted,500,'middle')}

<path d="M96 949H1824" stroke="#31434b" stroke-width="1"/>
${text(960,1010,'動いた先の映像を受け取り、判断と飛行を繰り返す',32,fg,500,'middle')}
</svg>`;
fs.writeFileSync(path.join(out,'mechanism_unified.svg'),svg);
fs.writeFileSync(path.join(out,'mechanism_unified.html'),`<!DOCTYPE html><html lang="ja"><meta charset="utf-8"><style>html,body{margin:0;width:1920px;height:1080px;background:${bg};overflow:hidden}svg{display:block}</style>${svg}</html>`);
console.log(path.join(out,'mechanism_unified.svg'));
