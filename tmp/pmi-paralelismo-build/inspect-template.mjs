import fs from 'node:fs/promises';
import {FileBlob, PresentationFile} from '@oai/artifact-tool';
const path='C:/Users/rafae_9y1k772/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-light-mode/assets/reference.pptx';
const deck=await PresentationFile.importPptx(await FileBlob.load(path));
const inspect=await deck.inspect({kind:'slide,textbox,shape,chart,table,layout',maxChars:250000});
await fs.writeFile('tmp/pmi-paralelismo-build/reference-inspect.ndjson',inspect.ndjson);
const shapes=deck.slides.items.map((slide,i)=>({slide:i+1,id:slide.id,shapes:slide.shapes.items.map(s=>({id:s.id,name:s.name,text:String(s.text),position:s.position,style:s.text.style})),charts:slide.charts.items.map(c=>({id:c.id,position:c.position}))}));
await fs.writeFile('tmp/pmi-paralelismo-build/reference-objects.json',JSON.stringify(shapes,null,2));
console.log('Inspeção salva: '+shapes.length+' slides.');
