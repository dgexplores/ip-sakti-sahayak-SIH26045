/** UI strings in the scripts people actually read.
 *
 * The language switch used to change three strings, and only between
 * romanised Hinglish ("Aapka sawaal") and English. Picking தமிழ் changed
 * nothing at all, so the multilingual claim did not survive a single click.
 * Hindi now renders in Devanagari and Tamil in Tamil script.
 *
 * Legal terms stay in Latin script on purpose: the problem statement
 * requires "Sec 3(p)", "TKDL", "Patents Act" and similar to be preserved
 * verbatim so a user can match them against the official record.
 */

export const LANGS = [
  { id: "hi", label: "हिन्दी", english: "Hindi" },
  { id: "en", label: "English", english: "English" },
  { id: "ta", label: "தமிழ்", english: "Tamil" },
] as const;

export type Lang = (typeof LANGS)[number]["id"];

type Strings = {
  tagline: string;
  headline: string;
  headlineAccent: string;
  subhead: string;
  step1: string;
  step2: string;
  step3: string;
  askTitle: string;
  askHint: string;
  examplesLabel: string;
  speak: string;
  speakHint: string;
  listening: string;
  listeningHint: string;
  voiceUnsupported: string;
  or: string;
  placeholder: string;
  send: string;
  sending: string;
  simpleMode: string;
  simpleModeHint: string;
  notSure: string;
  notSureHint: string;
  openTriage: string;
  closeTriage: string;
  answerIndia: string;
  answerWorld: string;
  splitTitle: string;
  splitHint: string;
  splitRun: string;
  splitLoading: string;
  splitNoData: string;
  simpleHeading: string;
  proofTitle: string;
  proofEmpty: string;
  proofHint: string;
  openSource: string;
  confidence: string;
  escalate: string;
  escalateSending: string;
  escalateDone: string;
  escalateDoneBody: string;
  escalateFailed: string;
  lowTrust: string;
  export: string;
  print: string;
  india: string;
  world: string;
  indiaSub: string;
  worldSub: string;
  free: string;
  offline: string;
  noFees: string;
  languages: string;
  backendOffline: string;
  loading: string;
  errorHint: string;
  disclaimer: string;
  glossaryTitle: string;
  footerNote: string;
  privacy: string;
  terms: string;
  skipLink: string;
  errTitle: string;
  errBody: string;
  errRetry: string;
  nfTitle: string;
  nfBody: string;
  nfBack: string;
};

const en: Strings = {
  tagline: "Ayurveda law helper",
  headline: "Your question, with",
  headlineAccent: "government proof",
  subhead: "Ask in your own words. Every answer quotes the real law and links to the official page. If we are not sure, we say so and send you to a human expert.",
  step1: "Ask your question",
  step2: "We search the law",
  step3: "Read the answer and its proof",
  askTitle: "Ask your question",
  askHint: "Speak or type, whichever is easier.",
  examplesLabel: "Or try one of these",
  speak: "Tap to speak",
  speakHint: "Hindi, Tamil or English",
  listening: "Listening, tap to stop",
  listeningHint: "We can hear you",
  voiceUnsupported: "This browser cannot take voice input. Please type your question below instead.",
  or: "or",
  placeholder: "Type your question here, in your own words",
  send: "Get the answer",
  sending: "Checking the law…",
  simpleMode: "Simple words",
  simpleModeHint: "Add a plain-language version",
  notSure: "Not sure how to describe your product?",
  notSureHint: "Answer 3 quick questions and we will work it out.",
  openTriage: "Answer 3 questions",
  closeTriage: "Close",
  answerIndia: "India: the answer",
  answerWorld: "International: the answer",
  splitTitle: "See the two laws separately — the problem statement's rule",
  splitHint: "India and the World are never mixed. That separation is exactly what the problem statement asks us to prove.",
  splitRun: "India vs World, side by side",
  splitLoading: "Fetching both…",
  splitNoData: "No data yet — press the button",
  simpleHeading: "In simple words",
  proofTitle: "Proof for every line",
  proofEmpty: "Your proof will appear here",
  proofHint: "Each answer is backed by the actual Act, Rule or Treaty, with a link to the government page.",
  openSource: "Open the official page",
  confidence: "confidence",
  escalate: "Send to a human expert",
  escalateSending: "Sending…",
  escalateDone: "Sent to an expert",
  escalateDoneBody: "Your question, the proof and the confidence score were all forwarded. Your data is kept safely under DPDP rules.",
  escalateFailed: "Could not send this to an expert. Please try again in a moment.",
  lowTrust: "Confidence is low. Sending this to a human expert is the safer choice.",
  export: "Download report",
  print: "Print",
  india: "INDIA",
  world: "INTERNATIONAL",
  indiaSub: "Indian law",
  worldSub: "Foreign law",
  free: "Free",
  offline: "Works offline",
  noFees: "No lawyer fees",
  languages: "3 languages",
  backendOffline: "server offline",
  loading: "loading…",
  errorHint: "Could not reach the server. Is the backend running?",
  disclaimer: "Information only, not legal advice. Please check the source links before you file anything.",
  glossaryTitle: "Words you will meet",
  footerNote: "Citation-grounded guidance, not legal advice. Verify against the official sources.",
  privacy: "Privacy",
  terms: "Terms",
  skipLink: "Skip to content",
  errTitle: "Something went wrong",
  errBody: "Something broke on this page. Your question and the answer trace are still safe — this is only a display error. Try again, or refresh if it keeps happening.",
  errRetry: "Try again",
  nfTitle: "Page not found",
  nfBody: "The page you asked for does not exist, or it was moved.",
  nfBack: "Back to Sahayak",
};

const hi: Strings = {
  tagline: "आयुर्वेद कानून सहायक",
  headline: "आपका सवाल,",
  headlineAccent: "सरकारी सबूत के साथ",
  subhead: "अपने शब्दों में पूछिए। हर जवाब में असली कानून की लाइन और सरकारी लिंक मिलेगा। अगर हमें पक्का पता न हो, तो हम साफ़ बता देंगे और आपको जानकार के पास भेज देंगे।",
  step1: "अपना सवाल पूछिए",
  step2: "हम कानून ढूँढते हैं",
  step3: "जवाब और सबूत पढ़िए",
  askTitle: "अपना सवाल पूछिए",
  askHint: "बोलिए या लिखिए, जो आसान लगे।",
  examplesLabel: "या इनमें से कोई चुनिए",
  speak: "बोलने के लिए दबाइए",
  speakHint: "हिन्दी, तमिल या अंग्रेज़ी",
  listening: "सुन रहे हैं, रोकने के लिए दबाइए",
  listeningHint: "हमें आपकी आवाज़ आ रही है",
  voiceUnsupported: "यह ब्राउज़र आवाज़ नहीं ले सकता। नीचे अपना सवाल टाइप कीजिए।",
  or: "या",
  placeholder: "अपना सवाल यहाँ लिखिए, अपने ही शब्दों में",
  send: "जवाब पाइए",
  sending: "कानून जाँच रहे हैं…",
  simpleMode: "आसान भाषा",
  simpleModeHint: "सरल शब्दों में भी दिखाइए",
  notSure: "अपने प्रोडक्ट को समझाना मुश्किल लग रहा है?",
  notSureHint: "3 छोटे सवालों के जवाब दीजिए, हम खुद पता लगा लेंगे।",
  openTriage: "3 सवालों के जवाब दीजिए",
  closeTriage: "बंद कीजिए",
  answerIndia: "भारत: आपका जवाब",
  answerWorld: "विदेश: आपका जवाब",
  splitTitle: "दोनों कानून अलग-अलग देखिए — PS का नियम",
  splitHint: "भारत और विदेश कभी नहीं मिलते। यही अलगाव problem statement साबित करने को कहता है।",
  splitRun: "भारत बनाम विदेश, साथ-साथ",
  splitLoading: "दोनों ला रहे हैं…",
  splitNoData: "अभी कोई डेटा नहीं — बटन दबाइए",
  simpleHeading: "आसान शब्दों में",
  proofTitle: "हर लाइन का सबूत",
  proofEmpty: "आपका सबूत यहाँ दिखेगा",
  proofHint: "हर जवाब के पीछे असली Act, Rule या Treaty होता है, साथ में सरकारी पेज का लिंक।",
  openSource: "सरकारी पेज खोलिए",
  confidence: "भरोसा",
  escalate: "जानकार के पास भेजिए",
  escalateSending: "भेजा जा रहा है…",
  escalateDone: "जानकार के पास भेज दिया",
  escalateDoneBody: "आपका सवाल, सबूत और भरोसे का स्कोर, सब भेज दिया गया है। आपकी जानकारी DPDP नियमों के तहत सुरक्षित है।",
  escalateFailed: "यह जानकार के पास नहीं भेजा जा सका। थोड़ी देर बाद फिर कोशिश कीजिए।",
  lowTrust: "भरोसा कम है। इसे किसी जानकार के पास भेजना ज़्यादा सही रहेगा।",
  export: "रिपोर्ट डाउनलोड कीजिए",
  print: "प्रिंट कीजिए",
  india: "भारत",
  world: "विदेश",
  indiaSub: "भारत के नियम",
  worldSub: "विदेश के नियम",
  free: "मुफ़्त",
  offline: "बिना इंटरनेट भी",
  noFees: "वकील की फ़ीस नहीं",
  languages: "3 भाषाएँ",
  backendOffline: "सर्वर बंद है",
  loading: "लोड हो रहा है…",
  errorHint: "सर्वर से बात नहीं हो पाई। क्या backend चालू है?",
  disclaimer: "यह सिर्फ़ जानकारी है, कानूनी सलाह नहीं। फ़ाइल करने से पहले सरकारी लिंक ज़रूर देखिए।",
  glossaryTitle: "ये शब्द आपको मिलेंगे",
  footerNote: "हर जवाब असली कानून के हवाले से, कानूनी सलाह नहीं। सरकारी स्रोत से ज़रूर मिलाइए।",
  privacy: "निजता",
  terms: "शर्तें",
  skipLink: "सीधे सामग्री पर जाइए",
  errTitle: "कुछ गड़बड़ हो गई",
  errBody: "इस पेज पर कुछ टूट गया। आपका सवाल और जवाब का रिकॉर्ड सुरक्षित है — यह सिर्फ़ दिखने की गड़बड़ है। फिर कोशिश कीजिए, और बार-बार हो तो पेज रीफ़्रेश कीजिए।",
  errRetry: "फिर कोशिश कीजिए",
  nfTitle: "यह पेज नहीं मिला",
  nfBody: "आपने जो पेज माँगा है वह मौजूद नहीं है, या हटा दिया गया है।",
  nfBack: "सहायक पर वापस जाइए",
};

const ta: Strings = {
  tagline: "ஆயுர்வேத சட்ட உதவியாளர்",
  headline: "உங்கள் கேள்வி,",
  headlineAccent: "அரசு ஆதாரத்துடன்",
  subhead: "உங்கள் சொந்த வார்த்தைகளில் கேளுங்கள். ஒவ்வொரு பதிலிலும் உண்மையான சட்ட வரி மற்றும் அரசு இணைப்பு இருக்கும். எங்களுக்கு உறுதியாகத் தெரியாவிட்டால், அதைத் தெளிவாகச் சொல்லி உங்களை நிபுணரிடம் அனுப்புவோம்.",
  step1: "உங்கள் கேள்வியைக் கேளுங்கள்",
  step2: "நாங்கள் சட்டத்தைத் தேடுகிறோம்",
  step3: "பதிலையும் ஆதாரத்தையும் படியுங்கள்",
  askTitle: "உங்கள் கேள்வியைக் கேளுங்கள்",
  askHint: "பேசுங்கள் அல்லது எழுதுங்கள், எது எளிதோ அது.",
  examplesLabel: "அல்லது இவற்றில் ஒன்றைத் தேர்ந்தெடுங்கள்",
  speak: "பேச அழுத்துங்கள்",
  speakHint: "இந்தி, தமிழ் அல்லது ஆங்கிலம்",
  listening: "கேட்கிறோம், நிறுத்த அழுத்துங்கள்",
  listeningHint: "உங்கள் குரல் கேட்கிறது",
  voiceUnsupported: "இந்த உலாவியில் குரல் உள்ளீடு இல்லை. கீழே உங்கள் கேள்வியை எழுதுங்கள்.",
  or: "அல்லது",
  placeholder: "உங்கள் கேள்வியை இங்கே எழுதுங்கள், உங்கள் சொந்த வார்த்தைகளில்",
  send: "பதிலைப் பெறுங்கள்",
  sending: "சட்டத்தைச் சரிபார்க்கிறோம்…",
  simpleMode: "எளிய வார்த்தைகள்",
  simpleModeHint: "எளிய மொழியிலும் காட்டுங்கள்",
  notSure: "உங்கள் பொருளை விவரிக்க சிரமமாக உள்ளதா?",
  notSureHint: "3 சிறிய கேள்விகளுக்குப் பதில் சொல்லுங்கள், நாங்கள் கண்டுபிடிக்கிறோம்.",
  openTriage: "3 கேள்விகளுக்குப் பதில் சொல்லுங்கள்",
  closeTriage: "மூடுங்கள்",
  answerIndia: "இந்தியா: உங்கள் பதில்",
  answerWorld: "வெளிநாடு: உங்கள் பதில்",
  splitTitle: "இரு சட்டங்களையும் தனித்தனியாகப் பாருங்கள் — PS விதி",
  splitHint: "இந்தியாவும் வெளிநாடும் ஒருபோதும் கலக்காது. அந்தப் பிரிவுதான் problem statement நிரூபிக்கச் சொல்வது.",
  splitRun: "இந்தியா vs வெளிநாடு, பக்கவாட்டில்",
  splitLoading: "இரண்டையும் கொண்டு வருகிறோம்…",
  splitNoData: "இன்னும் தரவு இல்லை — பொத்தானை அழுத்துங்கள்",
  simpleHeading: "எளிய வார்த்தைகளில்",
  proofTitle: "ஒவ்வொரு வரிக்கும் ஆதாரம்",
  proofEmpty: "உங்கள் ஆதாரம் இங்கே தெரியும்",
  proofHint: "ஒவ்வொரு பதிலுக்கும் பின்னால் உண்மையான Act, Rule அல்லது Treaty இருக்கும், அரசு பக்க இணைப்புடன்.",
  openSource: "அரசு பக்கத்தைத் திறக்கவும்",
  confidence: "நம்பிக்கை",
  escalate: "நிபுணரிடம் அனுப்புங்கள்",
  escalateSending: "அனுப்பப்படுகிறது…",
  escalateDone: "நிபுணரிடம் அனுப்பப்பட்டது",
  escalateDoneBody: "உங்கள் கேள்வி, ஆதாரம் மற்றும் நம்பிக்கை மதிப்பெண் அனைத்தும் அனுப்பப்பட்டன. உங்கள் தகவல் DPDP விதிகளின்படி பாதுகாப்பாக உள்ளது.",
  escalateFailed: "இதை நிபுணரிடம் அனுப்ப முடியவில்லை. சிறிது நேரம் கழித்து மீண்டும் முயற்சி செய்யுங்கள்.",
  lowTrust: "நம்பிக்கை குறைவாக உள்ளது. இதை ஒரு நிபுணரிடம் அனுப்புவது பாதுகாப்பானது.",
  export: "அறிக்கையைப் பதிவிறக்கவும்",
  print: "அச்சிடவும்",
  india: "இந்தியா",
  world: "வெளிநாடு",
  indiaSub: "இந்திய சட்டம்",
  worldSub: "வெளிநாட்டுச் சட்டம்",
  free: "இலவசம்",
  offline: "இணையம் இல்லாமலும்",
  noFees: "வழக்கறிஞர் கட்டணம் இல்லை",
  languages: "3 மொழிகள்",
  backendOffline: "சர்வர் இயங்கவில்லை",
  loading: "ஏற்றப்படுகிறது…",
  errorHint: "சர்வரைத் தொடர்பு கொள்ள முடியவில்லை. backend இயங்குகிறதா?",
  disclaimer: "இது தகவல் மட்டுமே, சட்ட ஆலோசனை அல்ல. பதிவு செய்வதற்கு முன் அரசு இணைப்புகளைச் சரிபார்க்கவும்.",
  glossaryTitle: "நீங்கள் சந்திக்கும் சொற்கள்",
  footerNote: "மேற்கோள்களுடன் கூடிய வழிகாட்டல், சட்ட ஆலோசனை அல்ல. அரசு ஆதாரங்களுடன் சரிபார்க்கவும்.",
  privacy: "தனியுரிமை",
  terms: "விதிமுறைகள்",
  skipLink: "உள்ளடக்கத்திற்குச் செல்லவும்",
  errTitle: "ஏதோ தவறு நடந்தது",
  errBody: "இந்தப் பக்கத்தில் ஏதோ உடைந்தது. உங்கள் கேள்வியும் பதிலின் பதிவும் பாதுகாப்பாக உள்ளன — இது காட்சிப் பிழை மட்டுமே. மீண்டும் முயற்சி செய்யுங்கள், தொடர்ந்தால் பக்கத்தைப் புதுப்பியுங்கள்.",
  errRetry: "மீண்டும் முயற்சி செய்யுங்கள்",
  nfTitle: "இந்தப் பக்கம் இல்லை",
  nfBody: "நீங்கள் கேட்ட பக்கம் இல்லை, அல்லது அது நகர்த்தப்பட்டுவிட்டது.",
  nfBack: "சகாயக்-க்குத் திரும்புங்கள்",
};

const DICT: Record<Lang, Strings> = { en, hi, ta };

export function t(lang: string): Strings {
  return DICT[(lang as Lang)] ?? en;
}

/** The chosen language survives a reload.
 *
 * It used to live only in React state, so a Tamil reader who refreshed the
 * page was silently dropped back into Hindi — on a product whose headline
 * claim is that it speaks the reader's language. The error and 404 pages are
 * separate render trees and cannot see that state at all, so they read this.
 */
const LANG_STORAGE_KEY = "ip-sakti-lang";

export function readStoredLang(): Lang | null {
  if (typeof window === "undefined") return null;
  try {
    const v = window.localStorage.getItem(LANG_STORAGE_KEY);
    return LANGS.some((l) => l.id === v) ? (v as Lang) : null;
  } catch {
    // Private browsing or storage blocked. Falling back is correct.
    return null;
  }
}

export function storeLang(lang: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LANG_STORAGE_KEY, lang);
  } catch {
    /* the choice simply will not persist; nothing to recover from */
  }
}

/** Example questions, shown in the reader's own script.
 *  The `q` sent to the API stays English: the corpus is English, so
 *  translating the query would only hurt retrieval.
 */
export const EXAMPLES = [
  {
    icon: "classical",
    jurisdiction: "india",
    q: "Is classical Ashwagandha churna as per Charaka Samhita patentable in India?",
    label: {
      en: "Can I patent an old recipe?",
      hi: "क्या पुराने नुस्खे का पेटेंट हो सकता है?",
      ta: "பழைய மருந்துக்கு பேட்டன்ட் கிடைக்குமா?",
    },
  },
  {
    icon: "novel",
    jurisdiction: "india",
    q: "I made a novel Ashwagandha extract with 10x withanolide by new process, patentable?",
    label: {
      en: "I made something new",
      hi: "मैंने कुछ नया बनाया है",
      ta: "நான் புதிதாக ஒன்று செய்துள்ளேன்",
    },
  },
  {
    icon: "world",
    jurisdiction: "international",
    q: "WIPO GRATK disclosure requirement for PCT filing with Indian genetic resource",
    label: {
      en: "Selling abroad?",
      hi: "विदेश में बेचना है?",
      ta: "வெளிநாட்டில் விற்கலாமா?",
    },
  },
  {
    icon: "plant",
    jurisdiction: "india",
    q: "Do I need NBA approval to source aloe vera from Kerala for cosmetic export?",
    label: {
      en: "Do I need plant permission?",
      hi: "क्या पौधे के लिए मंज़ूरी चाहिए?",
      ta: "தாவரத்திற்கு அனுமதி தேவையா?",
    },
  },
] as const;

/** 3-question triage, in the reader's own script. */
type Triage = {
  step: string; q1: string; q1hint: string; q1yes: string; q1yesSub: string; q1no: string; q1noSub: string;
  q2: string; q2hint: string; q2yes: string; q2yesSub: string; q2no: string; q2noSub: string;
  q3: string; q3hint: string;
  submit: string; incomplete: string; footnote: string;
  resultTitle: string; done: string; nextSteps: string;
  cat: Record<string, string>;
};

const TRIAGE_DICT: Record<Lang, Triage> = {
  en: {
    step: "Step", q1: "Is this recipe in an old Ayurveda text?",
    q1hint: "Such as Charaka Samhita or the First Schedule.",
    q1yes: "Yes, it is in a book", q1yesSub: "Classical, Sec 3(p) bar applies",
    q1no: "No, it is new", q1noSub: "Not in a book, a patent may be possible",
    q2: "Did you change anything?", q2hint: "A new ingredient, a new ratio, or a new way of making it.",
    q2yes: "Yes, I changed it", q2yesSub: "Novel, a patent may be possible",
    q2no: "No, it is the same", q2noSub: "Same as the book",
    q3: "What will you sell it as?", q3hint: "Pick the closest one.",
    submit: "Show my IP and ABS position", incomplete: "Answer the 3 questions above",
    footnote: "3 taps, no typing. The result maps to the Patents Act, BDA 2023 and FSSAI, with proof.",
    resultTitle: "Your result", done: "3 steps done", nextSteps: "Next steps",
    cat: { classical: "Classical", proprietary: "Proprietary", phytopharmaceutical: "Phytopharmaceutical", new_drug: "New drug", ayurveda_aahar: "Ayurveda food", cosmetic: "Cosmetic", unknown: "Not sure" },
  },
  hi: {
    step: "चरण", q1: "क्या यह नुस्खा किसी पुरानी आयुर्वेद किताब में है?",
    q1hint: "जैसे चरक संहिता या First Schedule में।",
    q1yes: "हाँ, किताब में है", q1yesSub: "क्लासिकल, Sec 3(p) की रोक लगेगी",
    q1no: "नहीं, यह नया है", q1noSub: "किताब में नहीं, पेटेंट हो सकता है",
    q2: "क्या आपने कुछ बदला है?", q2hint: "नई चीज़, नया अनुपात, या बनाने का नया तरीका।",
    q2yes: "हाँ, बदला है", q2yesSub: "नया है, पेटेंट हो सकता है",
    q2no: "नहीं, वैसा ही है", q2noSub: "किताब जैसा ही",
    q3: "आप इसे किस रूप में बेचेंगे?", q3hint: "जो सबसे नज़दीक हो वह चुनिए।",
    submit: "मेरा IP और ABS दिखाइए", incomplete: "ऊपर के 3 सवालों के जवाब दीजिए",
    footnote: "3 टैप, कोई टाइपिंग नहीं। नतीजा Patents Act, BDA 2023 और FSSAI से जुड़ता है, सबूत के साथ।",
    resultTitle: "आपका नतीजा", done: "3 चरण पूरे", nextSteps: "अगला कदम",
    cat: { classical: "क्लासिकल", proprietary: "प्रोप्राइटरी", phytopharmaceutical: "फाइटोफार्मा", new_drug: "नई दवा", ayurveda_aahar: "आयुर्वेद आहार", cosmetic: "कॉस्मेटिक", unknown: "पता नहीं" },
  },
  ta: {
    step: "படி", q1: "இந்த மருந்து பழைய ஆயுர்வேத நூலில் உள்ளதா?",
    q1hint: "சரக சம்ஹிதை அல்லது First Schedule போன்றவற்றில்.",
    q1yes: "ஆம், நூலில் உள்ளது", q1yesSub: "பாரம்பரியம், Sec 3(p) தடை பொருந்தும்",
    q1no: "இல்லை, இது புதியது", q1noSub: "நூலில் இல்லை, பேட்டன்ட் கிடைக்கலாம்",
    q2: "நீங்கள் ஏதாவது மாற்றியுள்ளீர்களா?", q2hint: "புதிய பொருள், புதிய விகிதம், அல்லது புதிய தயாரிப்பு முறை.",
    q2yes: "ஆம், மாற்றியுள்ளேன்", q2yesSub: "புதியது, பேட்டன்ட் கிடைக்கலாம்",
    q2no: "இல்லை, அப்படியே உள்ளது", q2noSub: "நூலில் உள்ளது போலவே",
    q3: "எதாக விற்கப் போகிறீர்கள்?", q3hint: "மிக நெருக்கமானதைத் தேர்ந்தெடுக்கவும்.",
    submit: "என் IP மற்றும் ABS நிலையைக் காட்டு", incomplete: "மேலே உள்ள 3 கேள்விகளுக்குப் பதில் சொல்லுங்கள்",
    footnote: "3 தட்டல்கள், தட்டச்சு தேவையில்லை. முடிவு Patents Act, BDA 2023 மற்றும் FSSAI உடன் இணைகிறது, ஆதாரத்துடன்.",
    resultTitle: "உங்கள் முடிவு", done: "3 படிகள் முடிந்தன", nextSteps: "அடுத்த படி",
    cat: { classical: "பாரம்பரியம்", proprietary: "தனியுரிமை", phytopharmaceutical: "ஃபைட்டோஃபார்மா", new_drug: "புதிய மருந்து", ayurveda_aahar: "ஆயுர்வேத உணவு", cosmetic: "அழகுசாதனம்", unknown: "தெரியவில்லை" },
  },
};

export function tri(lang: string): Triage {
  return TRIAGE_DICT[(lang as Lang)] ?? TRIAGE_DICT.en;
}

/** Glossary definitions, one per reader language.
 *
 * The *keys* stay in Latin script on purpose — a reader has to be able to
 * match "Sec 3(p)" or "TKDL" against the official record, and the answer
 * text renders those tokens verbatim. Only the explanation is translated.
 * These used to live in `GlossaryTooltip.tsx` as English-only prose, so the
 * language switch left every tooltip in English.
 */
const GLOSSARY_DICT: Record<Lang, Record<string, string>> = {
  en: {
    "Sec 3(p)": "Patents Act bar: traditional knowledge is not patentable. Copy-paste from an old book gets no patent.",
    TKDL: "Traditional Knowledge Digital Library — a government database that blocks foreign patents by proving the knowledge was already public.",
    ABS: "Access & Benefit Sharing — if you used an Indian plant or Indian knowledge, you must share the benefit and get NBA or SBB permission.",
    BDA: "Biological Diversity Act 2023 — the law that governs use of India's biological resources.",
    NBA: "National Biodiversity Authority — approves foreign use of Indian plants.",
    SBB: "State Biodiversity Board — grants approval or receives intimation for Indian users.",
    GRATK: "WIPO treaty 2024 — you must disclose where the genetic resource or traditional knowledge came from when you file.",
    PCT: "Patent Cooperation Treaty — a single filing that starts the international route.",
    Classical: "The recipe exactly as it stands in the old texts (First Schedule), so the Sec 3(p) bar applies.",
    Proprietary: "The ratio, process or dose was changed from the classical form, so a patent may be possible.",
    Phytopharmaceutical: "A purified plant-based drug with four or more markers — the CDSCO pathway.",
  },
  hi: {
    "Sec 3(p)": "Patents Act की रोक: पारंपरिक ज्ञान का पेटेंट नहीं होता। पुरानी किताब से ज्यों-का-त्यों उतारा तो पेटेंट नहीं मिलेगा।",
    TKDL: "Traditional Knowledge Digital Library — सरकारी डेटाबेस, जो यह साबित करके विदेशी पेटेंट रोकता है कि यह ज्ञान पहले से सबके सामने था।",
    ABS: "Access & Benefit Sharing — भारतीय पौधा या भारतीय ज्ञान इस्तेमाल किया है तो लाभ बाँटना होगा और NBA या SBB की मंज़ूरी लेनी होगी।",
    BDA: "Biological Diversity Act 2023 — भारत के जैविक संसाधनों के इस्तेमाल का कानून।",
    NBA: "National Biodiversity Authority — भारतीय पौधों के विदेशी इस्तेमाल को मंज़ूरी देती है।",
    SBB: "State Biodiversity Board — भारतीय उपयोगकर्ताओं को मंज़ूरी देता है या सूचना लेता है।",
    GRATK: "WIPO संधि 2024 — फ़ाइल करते समय बताना होगा कि जैविक संसाधन या पारंपरिक ज्ञान कहाँ से आया।",
    PCT: "Patent Cooperation Treaty — एक ही फ़ाइलिंग से अंतरराष्ट्रीय रास्ता शुरू होता है।",
    Classical: "नुस्खा पुरानी किताबों (First Schedule) में जैसा है वैसा ही, इसलिए Sec 3(p) की रोक लगेगी।",
    Proprietary: "क्लासिकल रूप से अनुपात, प्रक्रिया या मात्रा बदली गई है, इसलिए पेटेंट हो सकता है।",
    Phytopharmaceutical: "चार या ज़्यादा मार्कर वाली शुद्ध पौधे से बनी दवा — CDSCO का रास्ता।",
  },
  ta: {
    "Sec 3(p)": "Patents Act தடை: பாரம்பரிய அறிவுக்குப் பேட்டன்ட் கிடையாது. பழைய நூலிலிருந்து அப்படியே எடுத்தால் பேட்டன்ட் கிடைக்காது.",
    TKDL: "Traditional Knowledge Digital Library — இந்த அறிவு முன்பே பொதுவில் இருந்தது என நிரூபித்து வெளிநாட்டுப் பேட்டன்ட்களைத் தடுக்கும் அரசு தரவுத்தளம்.",
    ABS: "Access & Benefit Sharing — இந்திய தாவரத்தையோ இந்திய அறிவையோ பயன்படுத்தினால் பயனைப் பங்கிட வேண்டும், NBA அல்லது SBB அனுமதி பெற வேண்டும்.",
    BDA: "Biological Diversity Act 2023 — இந்தியாவின் உயிரியல் வளங்களைப் பயன்படுத்துவதை நிர்வகிக்கும் சட்டம்.",
    NBA: "National Biodiversity Authority — இந்திய தாவரங்களின் வெளிநாட்டுப் பயன்பாட்டுக்கு அனுமதி அளிக்கிறது.",
    SBB: "State Biodiversity Board — இந்திய பயனர்களுக்கு அனுமதி அளிக்கிறது அல்லது தகவலைப் பெறுகிறது.",
    GRATK: "WIPO ஒப்பந்தம் 2024 — தாக்கல் செய்யும்போது உயிரியல் வளம் அல்லது பாரம்பரிய அறிவு எங்கிருந்து வந்தது எனத் தெரிவிக்க வேண்டும்.",
    PCT: "Patent Cooperation Treaty — ஒரே தாக்கலில் சர்வதேச வழி தொடங்குகிறது.",
    Classical: "பழைய நூல்களில் (First Schedule) உள்ளபடியே உள்ள மருந்து, எனவே Sec 3(p) தடை பொருந்தும்.",
    Proprietary: "பாரம்பரிய வடிவத்திலிருந்து விகிதம், முறை அல்லது அளவு மாற்றப்பட்டுள்ளது, எனவே பேட்டன்ட் கிடைக்கலாம்.",
    Phytopharmaceutical: "நான்கு அல்லது அதற்கு மேற்பட்ட மார்க்கர் கொண்ட தூய தாவர மருந்து — CDSCO வழி.",
  },
};

export function glossary(lang: string): Record<string, string> {
  return GLOSSARY_DICT[(lang as Lang)] ?? GLOSSARY_DICT.en;
}

/** The terms that get a tooltip, longest first so "Sec 3(p)" is not
 *  shadowed by a shorter overlapping key. */
export const GLOSSARY_TERMS = [
  "Phytopharmaceutical",
  "Proprietary",
  "Classical",
  "Sec 3(p)",
  "GRATK",
  "TKDL",
  "NBA",
  "SBB",
  "ABS",
  "BDA",
  "PCT",
] as const;
