// Every tour the app knows about.
//
// ready:true  = script/route/cues files exist and the picker will open it
// ready:false = listed but greyed out, the way an untranslated language is
//
// Do NOT flip ready by hand — `python3 add-tour.py <id>` builds the three data
// files and flips it for you, so the flag can never claim a tour that is not
// actually on disk.
window.__TOURS__ = [
  {id:"1.0", ready:true,  name:"Golden Circle Direct",
   sub:"BSÍ → Þingvellir → Geysir → Gullfoss → Kerið → BSÍ"},

  {id:"2.0", ready:true , name:"Golden Circle Snowmobiling",
   sub:"BSÍ → Þingvellir → Geysir → Gullfoss → BSÍ"},

  {id:"3.0", ready:true , name:"Golden Circle Lagoons",
   sub:"BSÍ → Þingvellir → Geysir → Gullfoss → BSÍ"},

  {id:"4.0", ready:true , name:"Golden Circle Friðheimar",
   sub:"Anticlockwise — BSÍ → Friðheimar → Gullfoss → Geysir → Þingvellir → BSÍ"},

  {id:"5.0", ready:true,  name:"South Coast",
   sub:"BSÍ → Hvolsvöllur → Sólheimajökull → Reynisfjara → Vík"},

  {id:"6.0", ready:true,  name:"South Coast Combo",
   sub:"BSÍ → Hvolsvöllur → Skógafoss → Reynisfjara → Vík"},

  {id:"7.0", ready:true , name:"Glacial Lagoon",
   sub:"BSÍ → Skógafoss → Kirkjubæjarklaustur → Jökulsárlón → Vík → Reykjavík"}
];
