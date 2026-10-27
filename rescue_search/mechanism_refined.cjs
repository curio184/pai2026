const fs=require('fs'),path=require('path');
const root=process.env.RESCUE_PROJECT_ROOT;
const out=path.join(root,'output/video/mechanism_review');
const asset=fs.readFileSync(path.join(root,'tmp/premium/opening/0060.jpg')).toString('base64');
const font=fs.readFileSync('C:/Windows/Fonts/NotoSansJP-VF.ttf').toString('base64');
const C={bg:'#091319',white:'#eef1ee',muted:'#a9b8be',cyan:'#7ccac6',gold:'#dfbf8a',line:'#31444d'};
const txt=(x,y,s,n=28,color=C.white,w=450,a='start')=>`<text x="${x}" y="${y}" font-size="${n}" fill="${color}" font-weight="${w}" text-anchor="${a}">${s}</text>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1920" height="1080" viewBox="0 0 1920 1080">
<metadata>Conceptual hardware architecture; wireless and physical integration are proposed, not a claim of completed real-hardware flight. Motion generation is called by mission-control software. Original StampFly studio rendering retained.</metadata>
<defs>
 <marker id="in" markerUnits="userSpaceOnUse" markerWidth="17" markerHeight="16" refX="15" refY="8" orient="auto"><path d="M0 0L16 8L0 16Z" fill="${C.cyan}"/></marker>
 <marker id="out" markerUnits="userSpaceOnUse" markerWidth="17" markerHeight="16" refX="15" refY="8" orient="auto"><path d="M0 0L16 8L0 16Z" fill="${C.gold}"/></marker>
 <linearGradient id="v" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="white" stop-opacity="0"/><stop offset=".13" stop-color="white"/><stop offset=".83" stop-color="white"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient>
 <mask id="m"><rect x="82" y="426" width="560" height="430" fill="url(#v)"/></mask>
</defs>
<style>@font-face{font-family:SlideSans;src:url(data:font/ttf;base64,${font}) format('truetype');font-weight:100 900}text{font-family:SlideSans,sans-serif;letter-spacing:.01em}</style>
<rect width="1920" height="1080" fill="${C.bg}"/>
${txt(96,153,'飛行制御のしくみ',57,C.white,560)}

${txt(1496,282,'「青い服の人を探して」',34,C.white,500,'middle')}
<path d="M1496 309V350" stroke="${C.cyan}" stroke-width="2" fill="none" marker-end="url(#in)"/>

${txt(96,387,'ドローン',37,C.white,550)}
${txt(320,387,'StampFly',28,C.muted,450)}
<g mask="url(#m)"><svg x="82" y="426" width="560" height="430" viewBox="620 155 1080 845" preserveAspectRatio="xMidYMid meet"><image width="1920" height="1080" xlink:href="data:image/jpeg;base64,${asset}"/></svg></g>
${txt(362,900,'姿勢を安定させて飛行',27,C.muted,400,'middle')}

${txt(913,472,'映像・機体の状態',32,C.cyan,500,'middle')}
<path d="M658 515H1178" stroke="${C.cyan}" stroke-width="3" fill="none" marker-end="url(#in)"/>
${txt(913,560,'無線で送信',25,C.muted,400,'middle')}
${txt(913,768,'飛行指令',32,C.gold,500,'middle')}
<path d="M1180 810H658" stroke="${C.gold}" stroke-width="3" fill="none" marker-end="url(#out)"/>
${txt(913,855,'無線で返信',25,C.muted,400,'middle')}

${txt(1180,387,'制御用PC',37,C.white,550)}
<rect x="1180" y="418" width="644" height="504" fill="#0e1b23" stroke="${C.line}" stroke-width="1"/>
${txt(1224,468,'制御プログラム',27,C.white,500)}
${txt(1224,511,'捜索の進行と送受信を管理',26,C.muted,400)}
<path d="M1496 541V582" stroke="${C.cyan}" stroke-width="2" fill="none" marker-end="url(#in)"/>
${txt(1496,661,'SmolVLA',51,C.white,500,'middle')}
${txt(1496,714,'映像と指示から、飛行動作を生成',27,C.cyan,450,'middle')}
<path d="M1496 749V810H1180" stroke="${C.gold}" stroke-width="2" fill="none"/>
${txt(1496,867,'飛行指令に変換',26,C.muted,400,'middle')}
</svg>`;
fs.writeFileSync(path.join(out,'mechanism_refined.svg'),svg);
fs.writeFileSync(path.join(out,'mechanism_refined.html'),`<!DOCTYPE html><html lang="ja"><meta charset="utf-8"><style>html,body{margin:0;width:1920px;height:1080px;background:${C.bg};overflow:hidden}svg{display:block}</style>${svg}</html>`);
console.log('REFINED_DIAGRAM_READY');
