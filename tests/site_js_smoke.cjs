// Execute the deployed site's actual JavaScript with a minimal DOM. No browser/network dependency.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/../site/index.html','utf8');
const dataMatch=html.match(/<script id="clinic-data" type="application\/json">([\s\S]*?)<\/script>/);
const scriptMatch=html.match(/<script>\s*('use strict';[\s\S]*?)<\/script>/);
assert(dataMatch&&scriptMatch,'embedded data and UI script');
const DATA=JSON.parse(dataMatch[1]);const N=DATA.clinics.length;const numFor=(k)=>DATA.clinics.filter(x=>['ongoing','both'].includes(x.care_model)&&x.display_status===k).length;const TOWNS=new Set(DATA.clinics.map(x=>x.community)).size;const countTown=t=>DATA.clinics.filter(x=>x.community===t).length;
class Node{
 constructor(tag='',cls='',text=''){this.tag=tag;this.className=cls;this.textContent=text;this.children=[];this.handlers={};this.value='all';this.href='';this.style={};this.attrs={};}
 prepend(x){this.children.unshift(x);return x}append(...xs){this.children.push(...xs)}showModal(){this.open=true}close(){this.open=false}remove(){}focus(){}select(){}click(){if(this.handlers.click)this.handlers.click()}set id(v){this._id=v;ids[v]=this}get id(){return this._id}replaceChildren(...nodes){this.children=[...nodes]}
 setAttribute(k,v){this.attrs[k]=v}addEventListener(k,callback){this.handlers[k]=callback}
 scrollIntoView(){}get innerText(){return this.textContent+' '+this.children.map(x=>x.innerText).join(' ')}
 get count(){return this.children.length}
}
const ids={};for(const m of html.matchAll(/\bid="([^"]+)"/g))ids[m[1]]=new Node(m[1]);
ids['clinic-data'].textContent=dataMatch[1];
const document={handlers:{},addEventListener(k,callback){this.handlers[k]=callback},getElementById(id){assert(ids[id],`missing id: ${id}`);return ids[id]},createElement(tag){return new Node(tag)},createElementNS(ns,tag){return new Node(tag)}};
const timers=[];const context={document,console,Math,Set,JSON,Intl,TextEncoder,setInterval(fn){timers.push(fn)}};
vm.runInNewContext(scriptMatch[1].replace('})();','globalThis.features={distanceTo,filtered,setFilter,chosen,filterControls,openEditor,reviewEdit,pdfBytes,docxBytes,csvBytes,exportRows,selectedClinics};})();'),context, {timeout:3000,filename:'site-inline.js'});
assert.equal(ids.mTotal.textContent,N);assert.equal(ids.mIntake.textContent,numFor('accepting'));assert.equal(ids.mLeads.textContent,numFor('reported'));
assert.equal(ids.results.children.length,N);assert.equal(ids.map.children.filter(x=>x.tag==='g').length,TOWNS);
context.features.setFilter('status',['accepting']);assert.equal(ids.results.children.length,numFor('accepting')+3);
context.features.setFilter('status',['reported']);assert.equal(ids.results.children.length,numFor('reported'));
context.features.setFilter('status',['all']);
ids.search.handlers.input({target:{value:'Oxfordia'}});const match=C=>C.filter(c=>c.name.toLowerCase().includes('oxfordia')).length;assert.equal(ids.results.children.length,match(DATA.clinics));
ids.reset.handlers.click();assert.equal(ids.results.children.length,N);
context.features.setFilter('town',['Tillsonburg']);assert.equal(ids.results.children.length,countTown('Tillsonburg'));
assert(!/home.address|residential address geocod|Google Map/i.test(ids.last.innerText));
ids.reset.handlers.click();ids.mapMode.handlers.change({target:{value:'clinics'}});assert(ids.mapDetail.textContent.includes('sourced clinic points'));assert(ids.map.children.some(n=>n.tag==='g'));context.features.setFilter('town',['Tillsonburg']);assert(ids.mapDetail.textContent.includes('filtered listings'));ids.mapMode.handlers.change({target:{value:'towns'}});ids.reset.handlers.click();
// Surrounding-area filtering uses clinic points, never a fallback town point or network service.
context.features.setFilter('town',['Tillsonburg']);assert(!ids.surrounding.disabled);
ids.surrounding.checked=true;ids.surrounding.handlers.change();
const radiusRows=context.features.filtered();assert(radiusRows.length>countTown('Tillsonburg')&&radiusRows.length<N);
assert(radiusRows.every(c=>c.community==='Tillsonburg'||(context.features.distanceTo(c)!==null&&context.features.distanceTo(c)<=25)));
assert(DATA.clinics.filter(c=>c.community==='Tillsonburg').every(c=>radiusRows.some(r=>r.id===c.id)),'nearby is a superset of selected-community listings');
assert(radiusRows.every((c,i)=>!i||(context.features.distanceTo(c)??Infinity)>=(context.features.distanceTo(radiusRows[i-1])??Infinity)));
assert(ids.results.innerText.includes('straight line'));assert(ids.distanceStatus.textContent.includes('cannot be checked'));
ids.downloadScope.value='filtered';assert.equal(context.features.exportRows().length,radiusRows.length);
const localUnknown=DATA.clinics.find(c=>!Number.isFinite(c.latitude));assert(localUnknown);context.features.setFilter('town',[localUnknown.community]);assert(context.features.filtered().some(c=>c.id===localUnknown.id));assert(context.features.exportRows().some(c=>c.id===localUnknown.id));assert(ids.results.innerText.includes('Distance unavailable'));assert(!ids.unlocatedList.innerText.includes(localUnknown.name));context.features.setFilter('town',['Tillsonburg']);
assert.equal(context.features.distanceTo({latitude:42.8654,longitude:-80.7228}),0);
assert.equal(context.features.distanceTo({latitude:null,longitude:null}),null);
assert.equal(context.features.distanceTo({latitude:100,longitude:0}),null);
assert(context.features.distanceTo({latitude:42.8654+25/6371*180/Math.PI,longitude:-80.7228})>24.9999);
context.features.setFilter('town',['Tillsonburg','Kitchener']);assert(context.features.filtered().length>radiusRows.length);
context.features.setFilter('status',['accepting']);assert(context.features.filtered().every(c=>c.display_status==='accepting'));
context.features.setFilter('town',[]);assert(ids.surrounding.disabled);assert.equal(context.features.filtered().length,numFor('accepting')+3);
ids.reset.handlers.click();assert.equal(context.features.filtered().length,N);assert(ids.surrounding.disabled);assert(!ids.surrounding.checked);
console.log('PASS: surrounding-area inclusion, sort, missing/invalid coordinates, multiple communities, combined filters, filtered export and reset');
console.log(`PASS: ${N} records; ${numFor("accepting")} direct; ${numFor("reported")} reported; clinic filters and ${TOWNS} SVG markers; no patient-address entry`);

// Exercise the actual export and editor code, with a one-clinic selected subset.
const f=context.features;f.selectedClinics.add('c011');ids.downloadScope.value='selected';assert.equal(f.exportRows().length,1);assert.equal(f.exportRows()[0].id,'c011');
ids.downloadScope.value='all';assert.equal(f.exportRows().length,N);
const ox=DATA.clinics.find(c=>c.id==='c011');f.openEditor(ox);assert(ids.editDialog.open);ids['edit-phone'].value='519-555-0101';ids.editNote.value='Fixture source reviewed for phone correction.';f.reviewEdit();assert(!ids.editReview.hidden);assert(ids.editApprove.disabled);ids.editConfirm.value='wrong';ids.editAcknowledged.checked=true;ids.editConfirm.handlers.input();assert(ids.editApprove.disabled);ids.editConfirm.value='c011';ids.editConfirm.handlers.input();assert(!ids.editApprove.disabled);ids.editApprove.handlers.click();assert(!ids.editPublishSteps.hidden);assert.equal(JSON.parse(ids.editCode.value).changes.phone,'519-555-0101');assert.equal(ox.phone,'519-926-6752');
assert(f.csvBytes([{name:'=DANGEROUS',display_status:'unknown'}]).includes("'=DANGEROUS"));
if(process.env.EXPORT_FIXTURE_DIR){fs.mkdirSync(process.env.EXPORT_FIXTURE_DIR,{recursive:true});fs.writeFileSync(process.env.EXPORT_FIXTURE_DIR+'/selected.pdf',f.pdfBytes([ox]));fs.writeFileSync(process.env.EXPORT_FIXTURE_DIR+'/selected.docx',f.docxBytes([ox]));fs.writeFileSync(process.env.EXPORT_FIXTURE_DIR+'/all.pdf',f.pdfBytes(DATA.clinics));}
console.log('PASS: selected/all exports, CSV injection protection, edit review and typed confirmation; live data unchanged');
const researched=DATA.clinics.find(c=>c.online_review_text);
assert(researched,'research finding present');
assert(ids.results.children.some(card=>card.children.some(n=>n.className==='research')),'research disclosure rendered');
assert(f.csvBytes([researched]).includes(researched.online_review.finding.replace(/"/g,'""')),'CSV preserves research finding');
assert(f.pdfBytes([researched]).includes('Online research:'),'PDF preserves research context');
assert(new TextDecoder().decode(f.docxBytes([researched])).includes('Online research:'),'Word preserves research context');
console.log('PASS: research disclosures and CSV/PDF/Word research provenance');

// A continuously visible tab must downgrade without reload or focus changes.
const expired=f.exportRows().find(c=>c.display_status==='accepting');assert(expired);
expired.display_expires_on='2000-01-01';timers[0]();
assert.equal(expired.display_status,'needs_review');
assert.equal(ids.mIntake.textContent,numFor('accepting')-1);
assert(f.csvBytes([expired]).includes('Needs reconfirmation'));
assert(f.pdfBytes([expired]).includes('Needs reconfirmation'));
assert(new TextDecoder().decode(f.docxBytes([expired])).includes('Needs reconfirmation'));
// Direct export functions defend against expiry between selection and saving.
for(const encode of [f.csvBytes,f.pdfBytes,f.docxBytes]){
 const stale={...expired,display_status:'accepting'};encode([stale]);assert.equal(stale.display_status,'needs_review');
}
console.log('PASS: visible-tab timer and actual CSV/PDF/DOCX expiry guards');

// Exporting before the timer must also refresh visible cards/map, not swallow the change.
ids.reset.handlers.click();ids.downloadScope.value='all';
const raced=f.exportRows().find(c=>c.display_status==='accepting');assert(raced);
raced.display_expires_on='2000-01-01';f.exportRows();timers[0]();
const racedCard=ids.results.children.find(card=>card.innerText.includes(raced.name));
assert(racedCard&&racedCard.innerText.includes('Needs reconfirmation'));
assert(!racedCard.children.find(n=>n.className==='pills').children.some(n=>n.className==='pill accepting'));
console.log('PASS: export-first expiry also refreshes visible cards before timer');

// Detail-only corrections and new additions must render without false status claims.
assert(html.includes('Recent directory updates'));
assert(!ids.changeHistory.innerText.includes('null →'));
for (const entry of DATA.change_history.slice(0,10)) {
 if(entry.summary) assert(ids.changeHistory.innerText.includes(entry.summary),'Missing scoped change summary');
}
console.log('PASS: recent corrections render summaries without null statuses');

// Multiselect: OR within a field, AND across fields; actual checkbox change handlers.
ids.reset.handlers.click();
const ctl=f.filterControls;
function tick(id,value,checked){const input=ctl[id].inputs.find(x=>x[0]===value)[1];input.checked=checked;input.handlers.change()}
tick('status','reported',true);tick('status','waitlist',true);
const expected=DATA.clinics.filter(c=>['reported','waitlist'].includes(c.display_status));
assert.equal(ids.results.children.filter(x=>x.className==='item').length,expected.length);
assert(ids.statusSummary.textContent.includes('Waitlist'));
const twoTowns=[...new Set(expected.map(c=>c.community))].slice(0,2);
for(const t of twoTowns)tick('town',t,true);
assert.equal(ids.results.children.filter(x=>x.className==='item').length,expected.filter(c=>twoTowns.includes(c.community)).length);
ids.downloadScope.value='filtered';assert.equal(f.exportRows().length,expected.filter(c=>twoTowns.includes(c.community)).length);
ids.statusAll.handlers.click();assert.equal(f.chosen.status.length,0);
ids.townAll.handlers.click();assert.equal(f.exportRows().length,N);
ids.status.open=true;ids.status.handlers.keydown({key:'Escape'});assert.equal(ids.status.open,false);
ids.reset.handlers.click();assert.equal(f.chosen.status.length,0);assert.equal(f.chosen.town.length,0);
assert.equal(f.exportRows().length,N);
console.log('PASS: multiple statuses/communities, OR/AND combinations, filtered export, Show all, reset, Escape');

// Sourced HCC guidance is shared by the site and both document exporters.
assert(DATA.health_care_connect.text.includes('call 811'));
assert(DATA.health_care_connect.text.includes('keep your current provider'));
assert(DATA.health_care_connect.text.includes('register again by phone'));
assert(DATA.health_care_connect.text.includes('not guaranteed or immediate'));
assert(html.includes('Help finding a regular provider'));
assert(!html.includes('<!--HCC_GUIDANCE-->'));
assert(Buffer.from(f.docxBytes([ox])).toString().includes(DATA.health_care_connect.text));
assert(Buffer.from(f.pdfBytes([ox])).toString().includes('Health Care Connect'));
console.log('PASS: HCC guidance and provenance retained in website and PDF/Word exports');

// One search includes all service listings, with care labels rather than redundant views.
assert(!ids.purposeOngoing&&!ids.purposeWalkin&&!ids.care&&!ids.careSummary);
assert(!ids.metricsScope&&!html.includes('counterScope')&&!html.includes('In these results:'));
assert.deepEqual(Object.keys(f.chosen).sort(),['status','town']);
ids.reset.handlers.click();assert.equal(ids.results.children.filter(c=>c.className==='item').length,N);
for(const unknown of DATA.clinics.filter(c=>c.care_model==='unverified')){const card=ids.results.children.find(c=>c.innerText.includes(unknown.name));assert(card&&card.innerText.includes('Care model not verified'));assert(card.innerText.includes('Family-practice intake: Intake not confirmed'))}
assert(html.includes('Explore directory service listings'));

// Independent episodic and ongoing-care evidence remains visible, searchable and exportable.
ids.downloadScope.value='all';
const mixed=f.exportRows().find(c=>c.care_model==='both');assert(mixed);
const saved={walk:mixed.walk_in_review,ongoing:mixed.ongoing_care_review,status:mixed.display_status};
mixed.walk_in_review={status:'advertised',reviewed_on:'2026-11-18',finding:'Fixture: walk-in visits published; not live capacity.',eligibility:'Fixture eligibility is limited to adults.',sources:['https://example.org/walk-in']};
mixed.ongoing_care_review={reviewed_on:'2026-11-18',finding:'Fixture: separate ongoing-care evidence.',sources:['https://example.org/family-care']};
mixed.display_status='not_accepting';
f.setFilter('status',['not_accepting']);
const getMixed=()=>ids.results.children.find(c=>c.innerText.includes(mixed.name));
let card=getMixed();assert(card);assert(card.innerText.includes('Walk-in service advertised (check access)'));assert(card.innerText.includes('Family-practice intake: Not accepting'));
assert(card.innerText.includes('Fixture eligibility'));assert(card.innerText.includes('Family-care service review · 2026-11-18'));assert(card.innerText.includes('Walk-in evidence reviewed: 2026-11-18'));
assert.equal(card.children.find(c=>c.className==='pills').children[0].className,'pill not_accepting');
f.setFilter('status',['accepting']);assert(!getMixed(),'attachment-status filter still applies despite advertised walk-in service');
f.setFilter('status',[]);f.setFilter('town',[mixed.community]);for(const term of ['Fixture eligibility','separate ongoing-care evidence','walk-in visits published']){ids.search.handlers.input({target:{value:term}});assert(getMixed(),'service findings and eligibility are searchable')}
ids.search.handlers.input({target:{value:mixed.name}});assert(getMixed());
for(const status of ['uncertain','not_available']){mixed.walk_in_review.status=status;f.setFilter('status',[]);assert(getMixed().innerText.includes(status==='uncertain'?'Walk-in service needs verification':'Walk-in service not available'))}
delete mixed.walk_in_review;f.setFilter('status',[]);assert(getMixed().innerText.includes('Walk-in evidence review date: not recorded.'));
assert(getMixed().children.find(c=>c.className==='pills').children[0].innerText.includes('Family-practice intake: Not accepting'));
mixed.walk_in_review={status:'advertised',reviewed_on:'2026-11-18',finding:'Fixture: walk-in visits published; not live capacity.',eligibility:'Fixture eligibility is limited to adults.',sources:['https://example.org/walk-in']};
const csv=f.csvBytes([mixed]);assert(csv.includes('Family-practice intake: Not accepting'));assert(csv.includes('Walk-in service advertised'));assert(csv.includes('https://example.org/walk-in'));assert(csv.includes('https://example.org/family-care'));assert(csv.includes('Incomplete walk-in inventory'));
for(const text of [f.pdfBytes([mixed]),new TextDecoder().decode(f.docxBytes([mixed]))]){assert(text.includes('Family-practice intake:'));assert(text.includes('Walk-in evidence reviewed:'));assert(text.includes('Fixture eligibility'));assert(text.includes('https://example.org/walk-in'));assert(text.includes('https://example.org/family-care'))}
Object.assign(mixed,{walk_in_review:saved.walk,ongoing_care_review:saved.ongoing,display_status:saved.status});
ids.reset.handlers.click();ids.reset.handlers.click();assert.equal(f.chosen.town.length,0);assert.equal(f.chosen.status.length,0);assert.equal(ids.search.value,'');assert.equal(ids.results.children.filter(c=>c.className==='item').length,N);
ids.mapMode.handlers.change({target:{value:'clinics'}});assert(ids.map.children.some(c=>c.tag==='g'));ids.mapMode.handlers.change({target:{value:'towns'}});
console.log('PASS: single search includes unverified care; no hidden legacy controls; independent service evidence, search, attachment filter, repeated reset and all exports preserved');

// Reviewed TMC network applications are discoverable without office-intake upgrades.
ids.reset.handlers.click(); f.setFilter('status',['accepting']);
for(const id of ['c006','c007','c010']){
 const row=f.exportRows().find(c=>c.id===id);
 assert(row,'TMC network application must remain discoverable in applications filter');
 assert.equal(row.display_status,'reported');
 const card=ids.results.children.find(c=>c.innerText.includes(row.name));
 assert(card.innerText.includes('Network applications advertised; location not confirmed.'));
}
f.setFilter('status',['reported']);
for(const id of ['c006','c007','c010'])assert(f.exportRows().some(c=>c.id===id));
ids.reset.handlers.click();
console.log('PASS: TMC applications discoverability retains network-level uncertainty and lead classification');
