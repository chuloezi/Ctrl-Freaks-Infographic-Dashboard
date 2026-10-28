import analyticsData from './analytics-data.json';


const birthHistory={years:analyticsData.years, ...analyticsData.births};
function renderBirthHistory(kind){
 const isRate=kind==='rate', values=isRate?birthHistory.rates:birthHistory.counts, W=700,H=250,L=70,R=18,T=21,B=38,iw=W-L-R,ih=H-T-B;
 const min=Math.min(...values)*.95,max=Math.max(...values)*1.05;
 const x=i=>L+iw*i/(values.length-1),y=v=>T+ih-((v-min)/(max-min))*ih;
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${isRate?'Adjusted crude birth rate':'Registered live birth counts'} from 2019 to 2025">`;
 for(let j=0;j<=4;j++){let val=min+(max-min)*j/4,yy=y(val);svg+=`<line x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}" stroke="#e7e8df"/><text x="${L-10}" y="${yy+4}" text-anchor="end" fill="#829087" font-size="11">${isRate?val.toFixed(1):(val/1000).toFixed(0)+'k'}</text>`}
 birthHistory.years.forEach((yr,i)=>svg+=`<text x="${x(i)}" y="${H-10}" text-anchor="middle" fill="#66776f" font-size="11">${yr}</text>`);
 svg+=`<polyline fill="none" stroke="#18766c" stroke-width="3.5" stroke-linejoin="round" points="${values.map((v,i)=>x(i)+','+y(v)).join(' ')}"/>`;
 values.forEach((v,i)=>svg+=`<circle cx="${x(i)}" cy="${y(v)}" r="4.5" fill="#18766c" stroke="white" stroke-width="2"><title>${birthHistory.years[i]}: ${isRate?v.toFixed(1)+' per 1,000':v.toLocaleString('en-US')+' registered births'}</title></circle>`);
 document.getElementById('birthTrendChart').innerHTML=svg+'</svg>';
 document.getElementById('birthTrendHeadline').textContent=isRate?`${values[0].toFixed(1)} → ${values.at(-1).toFixed(1)}`:`${values[0].toLocaleString('en-US')} → ${values.at(-1).toLocaleString('en-US')}`;
 document.getElementById('birthTrendSubtitle').textContent=isRate?`Adjusted crude birth rate · births per 1,000 people · ${(values.at(-1)-values[0]).toFixed(1)} since ${birthHistory.years[0]}`:`Registered live births · ${(values.at(-1)-values[0]).toLocaleString('en-US')} (${(100*(values.at(-1)-values[0])/values[0]).toFixed(1)}%) since ${birthHistory.years[0]}`;
 document.querySelectorAll('[data-birth-measure]').forEach(b=>{let selected=b.dataset.birthMeasure===kind;b.classList.toggle('active',selected);b.setAttribute('aria-pressed',String(selected))});
}
function initBirthHistory(){
 document.getElementById('birthTrendRows').innerHTML=birthHistory.years.map((year,i)=>{let value=birthHistory.counts[i],prev=birthHistory.counts[i-1],delta=prev===undefined?null:value-prev,pct=prev===undefined?null:100*delta/prev;return `<tr><td>${year}</td><td>${value.toLocaleString('en-US')}</td><td class="${delta>=0?'trend-up':'trend-down'}">${delta===null?'—':(delta>0?'+':'')+delta.toLocaleString('en-US')}</td><td class="${pct>=0?'trend-up':'trend-down'}">${pct===null?'—':(pct>0?'+':'')+pct.toFixed(1)+'%'}</td></tr>`}).join('');
  renderBirthHistory('rate');
}



const vitalSeries={
 deaths:{...analyticsData.deaths,color:'#b65c3e',unit:'Adjusted crude death rate · deaths per 1,000 people'},
 marriages:{...analyticsData.marriages,color:'#18766c',unit:'Crude marriage rate · marriages per 1,000 people'}
};
function renderVital(name,measure){
 const data=vitalSeries[name], values=measure==='rate'?data.rates:data.counts;
 const W=700,H=250,L=70,R=18,T=21,B=38, iw=W-L-R, ih=H-T-B;
 const min=measure==='rate'?0:0, max=measure==='rate'?Math.ceil(Math.max(...values)*1.1*2)/2:Math.ceil(Math.max(...values)*1.15/10000)*10000;
 const x=i=>L+iw*i/(values.length-1),y=v=>T+ih-v/max*ih;
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${name} ${measure} from 2019 to 2025">`;
 for(let j=0;j<=4;j++){let v=max*j/4, yy=y(v);svg+=`<line x1="${L}" y1="${yy}" x2="${W-R}" y2="${yy}" stroke="#e7e8df"/><text x="${L-10}" y="${yy+4}" text-anchor="end" fill="#829087" font-size="11">${measure==='rate'?v.toFixed(1):(v/1000).toFixed(0)+'k'}</text>`}
 for(let i=0;i<values.length;i++)svg+=`<text x="${x(i)}" y="${H-10}" text-anchor="middle" fill="#66776f" font-size="11">${analyticsData.years[i]}</text>`;
 svg+=`<polyline fill="none" stroke="${data.color}" stroke-width="3.5" stroke-linejoin="round" points="${values.map((v,i)=>x(i)+','+y(v)).join(' ')}"/>`;
 values.forEach((v,i)=>svg+=`<circle cx="${x(i)}" cy="${y(v)}" r="4.5" fill="${data.color}" stroke="white" stroke-width="2"><title>${analyticsData.years[i]}: ${measure==='rate'?v.toFixed(1):v.toLocaleString('en-US')}</title></circle>`);
 document.getElementById(name+'HistoryChart').innerHTML=svg+'</svg>';
 let first=values[0],last=values[6],change=last-first;
 document.getElementById(name+'Headline').textContent=(measure==='rate'?first.toFixed(1)+' → '+last.toFixed(1):first.toLocaleString('en-US')+' → '+last.toLocaleString('en-US'));
 document.getElementById(name+'Subtitle').textContent=measure==='rate'?data.unit+' · '+(change>0?'+':'')+change.toFixed(1)+' since 2019':'Registered '+name+' · '+(change>0?'+':'')+change.toLocaleString('en-US')+' ('+(100*change/first).toFixed(1)+'%) since 2019';
 document.querySelectorAll(`[data-vital="${name}"]`).forEach(b=>{let selected=b.dataset.measure===measure;b.classList.toggle('active',selected);b.setAttribute('aria-pressed',String(selected))});
}
function initVital(name){let counts=vitalSeries[name].counts;document.getElementById(name+'HistoryRows').innerHTML=counts.map((v,i)=>{let delta=i?v-counts[i-1]:null,pct=i?100*delta/counts[i-1]:null;return `<tr><td>${2019+i}</td><td>${v.toLocaleString('en-US')}</td><td class="${delta>=0?'trend-up':'trend-down'}">${delta===null?'—':(delta>0?'+':'')+delta.toLocaleString('en-US')}</td><td class="${pct>=0?'trend-up':'trend-down'}">${pct===null?'—':(pct>0?'+':'')+pct.toFixed(1)+'%'}</td></tr>`}).join('');renderVital(name,'rate')}


const C={teal:'#18766c',rust:'#b65c3e',grid:'#e7e8df',text:'#829087'};
function lineChart(id,labels,series,max=100){let W=700,H=245,L=40,R=12,T=19,B=37,iw=W-L-R,ih=H-T-B;let x=i=>L+i*iw/(labels.length-1),y=v=>T+ih-v/max*ih;let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Trend chart: ${labels.join(', ')}">`;for(let j=0;j<=4;j++){let v=max*j/4,yy=y(v);s+=`<line x1="${L}" y1="${yy}" x2="${W-R}" y2="${yy}" stroke="${C.grid}"/><text x="${L-9}" y="${yy+4}" font-size="11" text-anchor="end" fill="${C.text}">${+v.toFixed(1)}</text>`}labels.forEach((v,i)=>s+=`<text x="${x(i)}" y="${H-11}" font-size="11" text-anchor="middle" fill="${C.text}">${v}</text>`);series.forEach((d,k)=>{let points=d.values.map((v,i)=>`${x(i)},${y(v)}`).join(' ');s+=`<polyline points="${points}" fill="none" stroke="${d.color}" stroke-width="3" stroke-linejoin="round"/>`;d.values.forEach((v,i)=>s+=`<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="${d.color}" stroke="white" stroke-width="1.5"><title>${labels[i]}: ${v}%</title></circle>`);s+=`<text x="${x(labels.length-1)-3}" y="${y(d.values.at(-1))-11}" text-anchor="end" font-weight="700" font-size="12" fill="${d.color}">${d.values.at(-1)}%</text>`});document.getElementById(id).innerHTML=s+'</svg>'}
function barChart(id,labels,values,max,color=C.teal){let W=700,H=245,L=39,R=7,T=22,B=50,iw=W-L-R,ih=H-T-B,bw=iw/values.length*.61,x=i=>L+(i+.5)*iw/values.length,y=v=>T+ih-v/max*ih;let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Bar chart">`;[0,.25,.5,.75,1].forEach(fr=>{let yy=y(fr*max);s+=`<line x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}" stroke="${C.grid}"/><text x="${L-6}" y="${yy+3}" text-anchor="end" font-size="10" fill="${C.text}">${Math.round(fr*max)}</text>`});values.forEach((v,i)=>{s+=`<rect x="${x(i)-bw/2}" y="${y(v)}" width="${bw}" height="${T+ih-y(v)}" fill="${color}" opacity="${i===values.indexOf(Math.max(...values))?1:.7}" rx="2"><title>${labels[i]}: ${v}</title></rect><text x="${x(i)}" y="${y(v)-6}" text-anchor="middle" font-size="10" fill="#405951">${v}</text><text x="${x(i)}" y="${H-13}" text-anchor="middle" font-size="10" fill="${C.text}">${labels[i]}</text>`});document.getElementById(id).innerHTML=s+'</svg>'}
function bars(id,items,max){document.getElementById(id).innerHTML=items.map(([name,v,color])=>`<div class="baritem"><span>${name}</span><div class="track"><div class="fill" style="width:${v/max*100}%;background:${color||C.teal}"></div></div><strong>${v.toLocaleString('en-US')}</strong></div>`).join('')}
export function initializeCharts(){ initBirthHistory();initVital("deaths");initVital("marriages");
const years=analyticsData.years.map(String), birth=analyticsData.registration.birthCompleteness, death=analyticsData.registration.deathCompleteness;
lineChart('trend',years,[{values:birth,color:C.teal},{values:death,color:C.rust}]);
lineChart('deathtrend',years,[{values:death,color:C.rust}],60);
const charts=analyticsData.supplemental;
const chart=(id,key,max,color)=>{const data=charts[key];if(data)barChart(id,data.labels,data.values,max,color);};
chart('ages','maternal_age',30);
chart('fertility','age_specific_fertility',190,C.rust);
chart('duration','divorce_duration',1200);
const province=charts.divorce_province;
if(province)bars('provinces',province.labels.map((name,i)=>[name,province.values[i]]),Math.max(...province.values));
const causeGroup=(heading,key,color)=>{const d=charts[key];return `<div class="smallcap">${heading}</div>`+d.labels.map((n,i)=>`<div class="baritem"><span>${n}</span><div class="track"><div class="fill" style="width:${d.values[i]}%;background:${color}"></div></div><strong>${d.values[i]}%</strong></div>`).join('');};
document.getElementById('causes').innerHTML=causeGroup('Facility','cause_facility',C.teal)+causeGroup('Community','cause_community',C.rust);



}
export {renderBirthHistory,renderVital};
