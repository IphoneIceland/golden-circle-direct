// Shown after a tour is chosen, before the script starts. Same for every tour.
window.__BRIEFING__ = {
  title: "Safety First",
  step: "Step 2 — please read",
  items: [
    {icon:"🦺", head:"Safety first", body:[
      "Let's hear the sound of safety: **\"Click Clickity Click\"**.",
      "Seatbelts on at all times — let's avoid turning this into a rollercoaster ride! 🎢"]},
    {icon:"⏰", head:"Time", body:[
      "**Respect the clock = respect the flock!**",
      "You're on time 5 minutes early. You're late if you're on time.",
      "Being late affects everyone."]},
    {icon:"🎤", head:"Respect", body:[
      "When the mic's on, keep the side chat down.",
      "You might not care about lava, but the person next to you didn't come all this way to hear about your lunch plans."]},
    {icon:"🚪", head:"The doors", body:[
      "Front door is a red carpet entrance — always open when we're at a standstill.",
      "At some stops the bus will be locked to keep your valuables safe."]},
    {icon:"🚽", head:"Toilets", body:[
      "Restroom facilities available at every stop."]},
    {icon:"📱", head:"Phones", body:[
      "On the road: set to vibrate (we love surprises, but not the ringtone kind!).",
      "At stops: let them sing loud and proud!"]},
    {icon:"🪫", head:"Charging", body:[
      "USB ports available for your gadgets."]},
    {icon:"🍔", head:"Food and drinks", body:[
      "Keep munchies for the stops — plenty of chances to grab a bite along the way.",
      "No hot or smelly food. All drinks need a lid."]},
    {icon:"🎮", head:"Drones", body:[
      "Got a drone? You need an **Icelandic permit** to fly it legally."]},
    {icon:"⛏️", head:"Pickpockets", body:[
      "Please be safe with your belongings today, folks — beware of pickpockets at all stops."]},
    {icon:"🧭", head:"The clock system for directions", body:[
      "**12 o'clock** = straight ahead (front of the bus)",
      "**3 o'clock** = to the right",
      "**9 o'clock** = to the left",
      "**6 o'clock** = straight behind",
      "Example: *\"Look at 9 o'clock to see Perlan\"* = look to your left."]}
  ]
};

// Step 1 — the welcome, shown before the safety briefing.
window.__WELCOME__ = {
  step: "Step 1 — welcome",
  title: "Welcome onboard",
  lead: "Here's your tour for today, laid out the way we'll actually drive it.",
  items: [
    {icon:"🚌", head:"Drive sections", body:["The stretches of road between stops. Stories to listen to while we roll."]},
    {icon:"📍", head:"Our stops today",  body:["Where we get off the bus. Tap any one along the top to jump to it."]},
    {icon:"👆", head:"Moving through it", body:["**Swipe left and right** on the text to move between parts, or use the arrows.",
                                                "The map at the bottom draws the road as we travel it."]}
  ]
};

// The languages the app will offer. English is live; the rest are queued.
window.__LANGS__ = [
  {code:"en", flag:"🇬🇧", name:"English",    live:true},
  {code:"de", live:true, flag:"🇩🇪", name:"Deutsch"},
  {code:"fr", live:true, flag:"🇫🇷", name:"Français"},
  {code:"es", live:true, flag:"🇪🇸", name:"Español"},
  {code:"it", live:true, flag:"🇮🇹", name:"Italiano"},
  {code:"pt", flag:"🇵🇹", name:"Português"},
  {code:"nl", live:true, flag:"🇳🇱", name:"Nederlands"},
  {code:"pl", flag:"🇵🇱", name:"Polski"},
  {code:"da", flag:"🇩🇰", name:"Dansk"},
  {code:"sv", flag:"🇸🇪", name:"Svenska"},
  {code:"no", flag:"🇳🇴", name:"Norsk"},
  {code:"fi", flag:"🇫🇮", name:"Suomi"},
  {code:"is", flag:"🇮🇸", name:"Íslenska"},
  {code:"zh", flag:"🇨🇳", name:"中文"},
  {code:"ja", flag:"🇯🇵", name:"日本語"},
  {code:"ko", flag:"🇰🇷", name:"한국어"},
  {code:"ru", flag:"🇷🇺", name:"Русский"},
  {code:"ar", flag:"🇸🇦", name:"العربية"},
  {code:"hi", flag:"🇮🇳", name:"हिन्दी"},
  {code:"tr", flag:"🇹🇷", name:"Türkçe"},
  {code:"he", flag:"🇮🇱", name:"עברית"}
];
