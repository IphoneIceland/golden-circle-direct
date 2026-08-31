// Every tour the app knows about.
//
// ready:true  = script/route/cues files exist and the picker will open it
// ready:false = listed but greyed out, the way an untranslated language is
//
// Do NOT flip ready by hand — `python3 add-tour.py <id>` builds the three data
// files and flips it for you, so the flag can never claim a tour that is not
// actually on disk.
window.__TOURS__ = [
  {id:"1.0", group:"Golden Circle", ready:true,  name:"Golden Circle Direct",
   sub:"BSÍ → Þingvellir → Geysir → Gullfoss → BSÍ", km:246, blocks:36},
  {id:"2.0", group:"Golden Circle", ready:true , name:"Golden Circle Snowmobiling",
   sub:"BSÍ → Þingvellir → Geysir → Gullfoss → BSÍ", km:230, min:221, blocks:37},
  {id:"3.0", group:"Golden Circle", ready:true , name:"Golden Circle Lagoons",
   sub:"BSÍ → Þingvellir → Geysir → Gullfoss → BSÍ", km:230, min:221, blocks:37},
  {id:"4.0", group:"Golden Circle", ready:true , name:"Golden Circle Friðheimar",
   sub:"Anticlockwise — BSÍ → Friðheimar → Gullfoss → Geysir → Þingvellir → BSÍ", km:237, min:222, blocks:36},
  {id:"5.0", group:"South Coast", ready:true,  name:"South Coast",
   sub:"BSÍ → Hvolsvöllur → Sólheimajökull → Reynisfjara → Vík", km:417, min:437, blocks:31},
  {id:"6.0", group:"South Coast", ready:true,  name:"South Coast Combo",
   sub:"BSÍ → Hvolsvöllur → Skógafoss → Reynisfjara → Vík", km:417, min:437, blocks:31},
  {id:"7.0", group:"South Coast", ready:true , name:"Glacial Lagoon",
   sub:"BSÍ → Skógafoss → Kirkjubæjarklaustur → Jökulsárlón → Vík → Reykjavík", km:765, min:782, blocks:43},
  {id:"9.0", group:"Snæfellsnes", ready:true, name:"Snæfellsnes North", sub:"BSÍ → Selvallafoss → Kirkjufell → Djúpalónssandur → Arnarstapi → Ytri-Tunga → BSÍ", km:450, min:451, blocks:38},
  {id:"10.0", group:"Snæfellsnes", ready:true , name:"Snæfellsnes South",
   sub:"BSÍ → Ytri-Tunga → Arnarstapi → Djúpalónssandur → Kirkjufell → BSÍ", km:450, min:451, blocks:37}
];
