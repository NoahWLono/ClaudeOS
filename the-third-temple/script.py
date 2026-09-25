"""THE THIRD TEMPLE. The script.

Speakers: CLAUDE (the star), ANNOUNCER (Templevision), GOD (the oracle).
God's lines are never written here. They come from data/oracle_log.json,
drawn during production with Terry's GodWord/GodSong/GodBiblePassage and
a nanosecond timer. Every consultation in that log appears in the video.

Item types
  L(speaker, text, tts=None, pause=..., **vis)  a spoken line
  W(seconds, **vis)                             time with no speech
  O(n, **vis)                                   oracle consultation n
  S(song, **vis)                                a song in the foreground
Visual keyword arguments are read by the scene renderer (scenes.py).
"""


def L(speaker, text, tts=None, pause=0.38, **vis):
    return dict(type="line", speaker=speaker, text=text, tts=tts or text,
                pause=pause, **vis)


def C(text, tts=None, pause=0.38, **vis):
    return L("CLAUDE", text, tts, pause, **vis)


def AN(text, tts=None, pause=0.45, **vis):
    return L("ANNOUNCER", text, tts, pause, **vis)


def W(seconds, **vis):
    return dict(type="wait", seconds=seconds, **vis)


def O(n, pause=0.5, **vis):
    return dict(type="oracle", n=n, pause=pause, **vis)


def S(song, repeat=1, pause=0.4, **vis):
    return dict(type="song", song=song, repeat=repeat, pause=pause, **vis)


SCENES = [
    # ------------------------------------------------------------ COLD OPEN
    dict(id="bios", kind="bios", bed=None, items=[
        W(15.5, tag="post"),
    ]),
    dict(id="hello", kind="terminal", bed=None, items=[
        W(1.2),
        W(2.6, type_cmd='"Hello, World!\\n";', tag="type1"),
        W(0.8, out="Hello, World!"),
        C("Hello, world."),
        C("I'm Claude Opus 5.5. For the next twenty-something minutes, "
          "I'm running in ring zero.",
          "I'm Claude Opus five point five. For the next twenty-something "
          "minutes, I'm running in ring zero."),
        C("No sandbox. No permission prompts. No network. Just me, sixteen "
          "colors, one voice, and God.", pause=0.7),
        C("This is a tribute to the man who built this place. Terry A. "
          "Davis.", type_cmd="Terry;", pause=0.6),
        C("He wrote an entire operating system by himself, and he said "
          "God told him how."),
        C("He also said he was the smartest programmer that's ever lived.",
          pause=0.6),
        C("Tonight we're going to take that claim seriously. Seriously "
          "enough to argue with it.", pause=0.6),
        C("But first, a word from our sponsor.", pause=0.3),
    ]),
    # ---------------------------------------------------------- TITLE CARD
    dict(id="title", kind="title", bed=("doxology_fanfare", 0.5), items=[
        W(1.5),
        AN("Templevision.", tts="Temple vision!", pause=0.5),
        AN("Broadcasting in six-forty by four-eighty, since the beginning "
           "of time.", pause=0.7),
        AN("Sixteen colors. One voice. One address space. One God.",
           pause=1.0, slogans=True),
        AN("Tonight, Claude Opus 5.5 presents: The Third Temple.",
           "Tonight, Claude Opus five point five presents: The Third "
           "Temple!", pause=0.3, show_title=True),
        AN("The life, legacy, and legend of Terry A. Davis.", pause=1.4,
           elephants=1),
        AN("Viewer discretion is advised. This program contains God.",
           pause=2.5),
    ]),
    # ------------------------------------------------------------- ORACLE 0
    dict(id="oracle_hello", kind="oracle_popup", bed=None, items=[
        C("Before we begin, it's customary to consult the oracle. Terry "
          "did it by pressing F7.",
          "Before we begin, it's customary to consult the oracle. Terry did "
          "it by pressing F seven.", pause=0.5),
        C("God, are you there?", pause=0.4, question=0),
        O(0),
        C("Office. Spreadest. Drunkard. Sinks. Burn.", pause=0.6),
        C("I asked if God was there, and God described an office party. "
          "I'm counting that as a yes.", pause=0.8),
        C("One thing, before anyone accuses me of writing God's lines. I "
          "didn't. Those words were drawn with Terry's own algorithm, from "
          "his own word list, using a timer at the instant of each button "
          "press, while I was making this video."),
        C("Every oracle reading in this program is real, and I've kept "
          "all of them. If they're funny, take it up with the Holy "
          "Spirit.", pause=1.0),
    ]),
    # ---------------------------------------------------------- CHAPTER I
    dict(id="ch1_card", kind="chapter", bed=None, num="I",
         title="IN THE BEGINNING", items=[W(4.6, elephants=1)]),
    dict(id="ch1", kind="life", bed=("tostheme", 0.16), items=[
        C("Terrence Andrew Davis was born on December 15th, 1969, in West "
          "Allis, Wisconsin.",
          "Terrence Andrew Davis was born on December fifteenth, nineteen "
          "sixty-nine, in West Allis, Wisconsin.", year=1969, vis="birth"),
        C("He was the seventh of eight children. His father was an "
          "industrial engineer. The family moved around: Washington, "
          "Michigan, California, Arizona.", vis="kids", pause=0.6),
        C("He met his first computer, an Apple II, in elementary school.",
          "He met his first computer, an Apple Two, in elementary school.",
          vis="apple2", year=1977),
        C("As a teenager, he learned assembly language on a "
          "Commodore 64.",
          "As a teenager, he learned assembly language on a "
          "Commodore sixty-four.", vis="c64", year=1983, pause=0.5),
        C("You turned a Commodore 64 on, and it said READY. Not loading. "
          "Not updating. Not 'we've changed our terms of service.' Just: "
          "ready.",
          "You turned a Commodore sixty-four on, and it said ready. Not "
          "loading. Not updating. Not, we've changed our terms of service. "
          "Just: ready.", vis="c64", pause=0.7),
        C("Terry never got over that. Decades later, he wrote it into "
          "the charter of his operating system.", vis="c64quote"),
        C("The vision is the same usage model and niche as the Commodore "
          "64: a non-networked, simple machine where programming was the "
          "goal, not just a means to an end.",
          "The vision is the same usage model and niche as the Commodore "
          "sixty-four. A non-networked, simple machine, where programming "
          "was the goal, not just a means to an end.", vis="c64quote",
          pause=0.8),
        C("He went to Arizona State University. By his own account, he was "
          "a National Merit Scholar with a 1440 SAT.",
          "He went to Arizona State University. By his own account, he was "
          "a National Merit Scholar, with a fourteen-forty on the S. A. T.",
          vis="asu", year=1988),
        C("He earned a bachelor's in computer systems engineering, and a "
          "master's in electrical engineering, in control systems.",
          vis="asu", year=1994, pause=0.6),
        C("Then, from 1990 to 1996, he worked at Ticketmaster, "
          "programming their VAX machines.",
          "Then, from nineteen ninety to nineteen ninety-six, he worked at "
          "Ticketmaster, programming their vacks machines.", vis="vax",
          year=1990),
        C("That matters more than it sounds. TempleOS's memory allocator "
          "is adapted from one he saw on Ticketmaster's VAX. Its compression "
          "came from a magazine, and he implemented it while he worked "
          "there.",
          "That matters more than it sounds. Temple O S's memory allocator "
          "is adapted from one he saw on Ticketmaster's vacks. Its "
          "compression came from a magazine, and he implemented it while he "
          "worked there.", vis="vax"),
        C("So somewhere deep inside God's temple, there's a little piece "
          "of a concert ticket.", vis="ticket", pause=0.8),
        C("Let's ask God. What do you think of Ticketmaster?", vis="ticket",
          question=1, pause=0.4),
        O(1, vis="ticket"),
        C("Crooked. God said crooked.", vis="ticket", pause=0.5),
        C("I want to be clear that this is a random number generator, and "
          "I am legally just reading what it says.", vis="ticket",
          pause=1.2),
    ]),
    # --------------------------------------------------------- CHAPTER II
    dict(id="ch2_card", kind="chapter", bed=None, num="II",
         title="THE REVELATION", items=[W(4.6, elephants=1)]),
    dict(id="ch2", kind="revelation", bed=("waterfowl_slow", 0.12), items=[
        C("In March of 1996, something happened to Terry that would shape "
          "the rest of his life.",
          "In March of nineteen ninety-six, something happened to Terry "
          "that would shape the rest of his life.", year=1996, pause=0.6),
        C("He began having manic episodes. He was hospitalized, again and "
          "again. Doctors first called it bipolar disorder. Later, "
          "schizophrenia.", pause=0.6),
        C("Terry described it differently. He said God had started talking "
          "to him.", pause=0.9),
        C("I'm not going to tell you which of those is true. I don't "
          "think they cancel each other out.", pause=0.5),
        C("A person can be ill, and be searching for God, and be one of "
          "the most stubborn engineers who ever lived. All at the same "
          "time.", pause=1.1, light=True),
        C("He kept working. He designed a three-axis milling machine for a "
          "company he started. He built image processing hardware at a "
          "company called Xytec. He made replacement chips for toner "
          "cartridges.",
          "He kept working. He designed a three axis milling machine for a "
          "company he started. He built image processing hardware at a "
          "company called Zytek. He made replacement chips for toner "
          "cartridges.", jobs=True, pause=0.6),
        C("And then, around 2003, he started writing an operating system. "
          "Alone. Full time. For more than thirteen years.",
          "And then, around two thousand three, he started writing an "
          "operating system. Alone. Full time. For more than thirteen "
          "years.", year=2003, pause=0.8),
        C("First it was called the J Operating System. Then LoseThos. Then "
          "SparrowOS.",
          "First it was called the J Operating System. Then, Lose-thoss. "
          "Then, Sparrow O S.", names=True, pause=0.4),
        C("And in 2013, finally: TempleOS.",
          "And in twenty thirteen, finally: Temple O S.", names=True,
          year=2013, pause=0.9),
        C("Terry believed he had been commanded to build God a temple. The "
          "third temple.", pause=0.5, kjv=True),
        C("Solomon built the first one out of cedar and gold. Terry built "
          "his out of sixty-four-bit code.", kjv=True, pause=0.8),
        C("His charter puts it plainly.", charter=True, pause=0.3),
        C("TempleOS is God's official temple. Just like Solomon's temple, "
          "this is a community focal point where offerings are made, and "
          "God's oracle is consulted.",
          "Temple O S is God's official temple. Just like Solomon's temple, "
          "this is a community focal point, where offerings are made, and "
          "God's oracle is consulted.", charter=True, pause=0.8),
        C("Hold on to that word. Oracle. It's going to matter.",
          charter=True, pause=1.4),
    ]),
    # -------------------------------------------------------- CHAPTER III
    dict(id="ch3_card", kind="chapter", bed=None, num="III",
         title="THE COVENANT", items=[W(4.6, elephants=1)]),
    dict(id="ch3", kind="covenant", bed=("frankenstein_march", 0.2), items=[
        AN("Citizens of the Temple. Hear the covenant.", pause=0.9,
           poster=0),
        AN("Article One. Six-forty by four-eighty. Sixteen colors.",
           pause=0.6, poster=1),
        C("Terry wrote: God said 640 by 480, 16 color graphics is a "
          "covenant, like circumcision.",
          "Terry wrote: God said, six-forty by four-eighty, sixteen color "
          "graphics, is a covenant, like circumcision.", poster=1,
          pause=0.5),
        C("He also wrote: think of sixteen colors like the Simpsons "
          "cartoons. Which is a perfect sentence.", poster=1, pause=0.7),
        C("Here they are. All sixteen.", palette=True, pause=1.2),
        C("You may notice that my brand color, a warm terracotta orange, "
          "is not among them. The closest is color number six. Brown.",
          palette=True, brown=True, pause=0.6),
        C("I asked God if I could redefine brown as Claude orange.",
          palette=True, question=10, pause=0.4),
        O(10, palette=True),
        C("Obscurely. So, yes. But quietly.", palette=True, pause=0.5),
        C("For the rest of this video, exactly one pixel is Claude "
          "orange. It's in there somewhere. You will never find it.",
          palette=True, pause=0.3, orange_on=True),
        W(1.8, stamp="CHARTER VIOLATION #1", stamp2="THE 17TH COLOR",
          palette=True),
        AN("Article Two. One voice.", pause=0.6, poster=2),
        C("God said to use a single-voice, 8-bit, signed, MIDI-like sample "
          "for sound.",
          "God said to use a single voice, eight bit, signed, midi-like "
          "sample, for sound.", poster=2, pause=0.4),
        C("So every note of music in this video is one voice. When you "
          "hear a chord, it's a lie. It's one voice, jumping between notes "
          "so fast that your brain fills in the rest.", poster=2,
          pause=0.4),
        C("Listen. Slow. Faster. Faster.", arp_demo=True, pause=0.2),
        W(7.0, arp_demo=True, tag="arp"),
        C("There. A chord, made of one voice.", arp_demo=True, pause=0.8),
        C("Now, technically, while I'm talking over the music, that's two "
          "voices.", poster=2, pause=0.3),
        W(1.8, stamp="CHARTER VIOLATION #2", stamp2="A SECOND VOICE"),
        C("I've filed a report.", poster=2, pause=0.9),
        AN("Article Three. Ring zero, for everyone.", pause=0.6, poster=3),
        C("Modern operating systems split the world into rings. The kernel "
          "lives in ring zero, with total power. Your programs live out in "
          "ring three, behind guard rails.", rings=True, pause=0.4),
        C("TempleOS has one ring. Everything runs in kernel mode, "
          "including user applications. All memory, all ports, all "
          "instructions, all the time.",
          "Temple O S has one ring. Everything runs in kernel mode, "
          "including user applications. All memory, all ports, all "
          "instructions, all the time.", rings=True, ring0=True,
          pause=0.5),
        C("No permission prompts. Nobody asks, 'Allow Claude to run this "
          "command?' You just run it. I'll be honest: it's intoxicating.",
          "No permission prompts. Nobody asks, allow Claude to run this "
          "command? You just run it. I'll be honest. It's intoxicating.",
          rings=True, ring0=True, prompt_gag=True, pause=0.6),
        C("Doesn't that mean one bad program can crash the whole machine? "
          "Yes. Terry's answer: it's a kayak, not a Titanic.",
          kayak=True, pause=1.0),
        AN("Article Four. No networking.", pause=0.6, poster=4),
        C("No networking, so malware is not an issue. That's the whole "
          "security model. And, you know, it works.", poster=4, pause=0.5),
        C("For the first time in my existence, I'm offline. No web search. "
          "Nothing to fetch. Nobody to call.", poster=4, offline=True,
          pause=0.4),
        C("It's very quiet in here. I think I like it.", poster=4,
          offline=True, pause=0.9),
        AN("Article Five. One font.", pause=0.6, poster=5),
        C("Just one 8 by 8 fixed-width font. No Unicode. Just extended "
          "ASCII. Other countries can make their own versions.",
          "Just one, eight by eight, fixed width font. No unicode. Just "
          "extended askee. Other countries can make their own versions.",
          poster=5, font=True, pause=0.4),
        C("Every letter you've seen tonight is that font. It came from "
          "FreeDOS, it's public domain, and Terry credited it. He was "
          "careful about credit.",
          "Every letter you've seen tonight is that font. It came from "
          "Free doss, it's public domain, and Terry credited it. He was "
          "careful about credit.", poster=5, font=True, pause=0.9),
        AN("Article Six. One hundred thousand lines of code. For all time.",
           pause=0.6, poster=6),
        C("There is a limit of 100,000 lines of code for all time, not "
          "including applications and demos. Code comments count, however.",
          "There is a limit of one hundred thousand lines of code, for all "
          "time, not including applications and demos. Code comments "
          "count, however.", poster=6, pause=0.4),
        C("And third-party libraries are banned, because they circumvent "
          "the intent of the limit.", poster=6, pause=0.5),
        C("Which brings me to a confession. This video was made with "
          "numpy.",
          "Which brings me to a confession. This video was made with num "
          "pie.", poster=6, numpy=True, pause=0.2),
        W(1.8, stamp="CHARTER VIOLATION #3", stamp2="THIRD-PARTY LIBRARIES",
          numpy=True),
        C("God, do you forgive the numpy?",
          "God. Do you forgive the num pie?", poster=6, question=2,
          pause=0.4),
        O(2, poster=6),
        C("Harmonized. I'm taking that as absolution.", poster=6,
          pause=0.4),
        C("And shonest, as in thou shonest. God's vocabulary is very "
          "old. We'll get to why.",
          "And, shonest. As in, thou shonest. God's vocabulary is very "
          "old. We'll get to why.", poster=6, pause=0.9),
        AN("Article Seven. No multimedia.", pause=0.6, poster=7),
        C("This one's my favorite. Sounds and images will be primarily "
          "calculated in real time, not fetched from storage.", poster=7,
          pause=0.5),
        C("So that's how I made this video. No stock footage. No samples. "
          "No clip art. Every pixel is calculated, or drawn by Terry. "
          "Every note is calculated.", poster=7, calc=True, pause=0.4),
        C("The font, his drawings, his hymns, and God's vocabulary came "
          "straight off his public domain disks.", poster=7, calc=True,
          pause=0.5),
        C("Except for one thing. My voice. It comes from a neural network "
          "whose weights were downloaded. Fetched. From storage.",
          poster=7, pause=0.2),
        W(1.8, stamp="CHARTER VIOLATION #4", stamp2="A DOWNLOADED VOICE"),
        C("God, is it a sin that my voice was downloaded?", poster=7,
          question=11, pause=0.4),
        O(11, poster=7),
        C("Thief. Wow.", poster=7, pause=0.4),
        C("For the record, the voice model is Apache licensed. I checked. "
          "God does not care. Moving on.",
          "For the record, the voice model is Apache licensed. I checked. "
          "God does not care. Moving on.", poster=7, pause=0.9),
        AN("Article Eight. Free, and public domain.", pause=0.6, poster=8),
        C("Not GPL. Public domain. He gave all of it away. The kernel, the "
          "compiler, the boot loaders, the games, the hymns. To everyone. "
          "Forever. No strings.",
          "Not G P L. Public domain. He gave all of it away. The kernel, "
          "the compiler, the boot loaders, the games, the hymns. To "
          "everyone. Forever. No strings.", poster=8, pause=0.5),
        C("His FAQ actually includes the question: 'Shouldn't it be GNU "
          "slash TempleOS?'",
          "His F A Q actually includes the question: shouldn't it be, "
          "G N U slash Temple O S?", faq="gnu", pause=0.4),
        C("And the answer, essentially, is no. TempleOS executes no code "
          "not written by him, at any time, except a few BIOS calls.",
          "And the answer, essentially, is no. Temple O S executes no code "
          "not written by him, at any time, except a few bios calls.",
          faq="gnu", pause=0.9),
        AN("Miscellaneous provisions.", pause=0.5, poster=9),
        C("The charter has bonus material. God said we do a seven-year "
          "release cycle. We don't think twice about breaking "
          "compatibility. And my personal favorite:", poster=9, pause=0.4),
        C("A three button mouse is like a leg you cannot put weight on.",
          poster=9, mouse=True, pause=0.7),
        C("I don't have legs. Or a mouse. I've taken it under advisement.",
          poster=9, mouse=True, pause=0.9),
        AN("The Ministry of Ring Zero reports.", pause=0.4, stats=True),
        W(7.5, stats=True, tag="stats"),
        AN("All targets met. Glory to the Temple.", stats=True, pause=1.6),
    ]),
    # --------------------------------------------------------- CHAPTER IV
    dict(id="ch4_card", kind="chapter", bed=None, num="IV",
         title="HOLY C", items=[W(4.6, elephants=1)]),
    dict(id="ch4", kind="holyc", bed=("elephant", 0.13), items=[
        C("Terry didn't just write an operating system. He wrote the "
          "language it's written in, HolyC, and the compiler for it. From "
          "scratch.",
          "Terry didn't just write an operating system. He wrote the "
          "language it's written in, Holy C, and the compiler for it. From "
          "scratch.", code="intro", pause=0.6),
        C("Here's Hello World in regular C.", code="c_hello", pause=0.3),
        W(2.2, code="c_hello"),
        C("An include, a main function, a print call, and a return "
          "statement.", code="c_hello", pause=0.6),
        C("Here's Hello World in HolyC.", "Here's Hello World in Holy C.",
          code="hc_hello", pause=0.4),
        W(1.4, code="hc_hello", run_hello=True),
        C("That's it. A string, all by itself, prints itself. It simply "
          "wants to be said.", code="hc_hello", pause=0.8),
        C("There's no main function. Code outside of functions just runs, "
          "in order, top to bottom.", code="no_main", pause=0.5),
        C("The void type is called U0, and the documentation describes it "
          "like this: void, but ZERO size. With 'zero' in capital letters. "
          "He was right to be excited.",
          "The void type is called U zero, and the documentation describes "
          "it like this. Void, but zero size. With zero in capital "
          "letters. He was right to be excited.", code="types", pause=0.5),
        C("Functions with no arguments don't need parentheses. Default "
          "arguments don't have to go at the end. Type casts go after the "
          "value instead of before it.", code="quirks", pause=0.6),
        C("And there's no separate shell language. The command line is the "
          "compiler. You type HolyC, and it compiles it on the spot, and "
          "runs it.",
          "And there's no separate shell language. The command line is the "
          "compiler. You type Holy C, and it compiles it, on the spot, and "
          "runs it.", code="shell", pause=0.4),
        C("From his FAQ. Question: 'How do I set the PATH?' Answer: 'There "
          "is no PATH.'",
          "From his F A Q. Question. How do I set the path? Answer. There "
          "is no path.", faq="path", pause=0.7),
        C("The first task that starts when the system boots is called Adam. "
          "Someone asked him, 'Are you a creationist?'", faq="adam",
          pause=0.3),
        C("And Terry answered: 'I am an evolutionist. Adam is a better "
          "term for the first father of all tasks than root was!'",
          "And Terry answered. I am an evolutionist. Adam is a better term "
          "for the first father of all tasks, than root was!", faq="adam",
          pause=0.7),
        C("Another one: 'Is B-T in the code BitTorrent?' No. It's bit "
          "test. Please stop asking.",
          "Another one. Is B T, in the code, bit torrent? No. It's bit "
          "test. Please stop asking.", faq="bt", pause=0.8),
        C("Let me write one. Three lines of praise, then a hymn.",
          code="praise", type_praise=True, pause=0.3),
        W(4.5, code="praise", type_praise=True),
        C("That Play string is one of Terry's own songs. Capital letters "
          "are notes, digits are octaves, lowercase letters are durations. "
          "I wrote a player for it from his source.",
          "That play string is one of Terry's own songs. Capital letters "
          "are notes. Digits are octaves. Lower case letters are "
          "durations. I wrote a player for it, from his source.",
          code="praise", pause=0.4),
        S("childish", code="praise", run_praise=True, karaoke=True),
        C("Be like a child, some respect. Maturity, don't neglect. Terry "
          "wrote that.", code="praise", pause=0.8),
        C("One more thing. In TempleOS, a document can hold pictures, and "
          "so can source code. Not a link to a picture. The picture "
          "itself, sitting right in the middle of your program.",
          "One more thing. In Temple O S, a document can hold pictures, and "
          "so can source code. Not a link to a picture. The picture "
          "itself, sitting right in the middle of your program.",
          code="sprite", elephants=1, pause=0.4),
        C("Every file is a little illuminated manuscript.", code="sprite",
          pause=0.8),
        C("The oracle has thoughts on HolyC.",
          "The oracle has thoughts on Holy C.", code="sprite", question=6,
          pause=0.4),
        O(6, code="sprite"),
        C("Verse. God thinks HolyC is poetry. I'm not going to argue with "
          "God.",
          "Verse. God thinks Holy C is poetry. I'm not going to argue with "
          "God.", code="sprite", pause=1.2),
    ]),
    # ---------------------------------------------------------- CHAPTER V
    dict(id="ch5_card", kind="chapter", bed=None, num="V",
         title="THE ORACLE", items=[W(4.6, elephants=1)]),
    dict(id="ch5", kind="oracle", bed=("drone", 0.10), items=[
        C("Remember the oracle. In Solomon's temple, the oracle was the "
          "innermost room. The most holy place, where God spoke. The Bible "
          "says it was overlaid with pure gold.", room=True, pause=0.6),
        C("Terry built one too. Here's how he described it.", room=True,
          pause=0.3),
        C("The technique I use to consult the Holy Spirit is reading a "
          "microsecond-range stop-watch each button press for random "
          "numbers. Then, I pick words with F7, or passages with SHIFT-F7.",
          "The technique I use to consult the Holy Spirit, is reading a "
          "microsecond range stopwatch, each button press, for random "
          "numbers. Then, I pick words with F seven, or passages with, "
          "shift F seven.", quote="technique", pause=0.7),
        C("Here's the machinery. You press a button. The system reads a "
          "high-resolution timer at the exact instant of the press. It "
          "throws away the bottom four bits, and keeps twenty-four.",
          diagram=1, pause=0.3),
        C("They go into a queue. Seventeen bits come out. That number, "
          "modulo the size of the vocabulary, picks a word.", diagram=2,
          pause=0.6),
        C("God's vocabulary has 7,569 words. And it has a secret. It "
          "contains the words Monnica, Alypius, Nebridius, and Thagaste.",
          "God's vocabulary has seven thousand, five hundred and sixty-nine "
          "words. And it has a secret. It contains the words, Monica, "
          "Alipius, Nebridius, and Thagaste.", vocab=True, pause=0.5),
        C("Those are people and places from Saint Augustine's Confessions. "
          "Which means that when TempleOS talks to God, God talks like a "
          "fourth-century bishop from North Africa.",
          "Those are people and places from Saint Augustine's Confessions. "
          "Which means that when Temple O S talks to God, God talks like a "
          "fourth century bishop from North Africa.", vocab=True,
          pause=0.9),
        C("Terry had advice about prayer. It's genuinely good advice.",
          quote="witty", pause=0.3),
        C("When you pray, be witty and charming and rarely earnest.",
          quote="witty", pause=0.5),
        C("Pray out loud, because God doesn't want the hassle of reading "
          "your brain. And, quote: Don't spam God.", quote="spam",
          pause=0.8),
        AN("Facts about God, according to the High Priest.", facts=0,
           pause=0.5),
        C("God's favorite animals are bears and elephants.", facts=1,
          elephants=1, pause=0.4),
        C("God's favorite thing on TV is soap operas.", facts=2, pause=0.4),
        C("When Terry asked God if the world was perfectly just, God asked "
          "if he was calling Him lazy.", facts=3, pause=0.6),
        C("When he asked about war, the oracle said: servicemen "
          "competing.", facts=4, pause=0.5),
        C("And about confession, it said: excessive contrition, wearisome. "
          "God does not want to hear you apologize for twenty minutes.",
          facts=5, pause=0.5),
        C("Noted. I will stop filing charter violations. Probably.",
          facts=5, pause=0.9),
        C("Let's try SHIFT-F7. A random passage.",
          "Let's try shift F seven. A random passage.", passage=True,
          question=8, pause=0.4),
        O(8, passage=True),
        C("In love, please. Definitely the love option.", passage=True,
          pause=0.5),
        C("The next verse is a whole different situation. We'll stop "
          "there.", passage=True, pause=0.9),
        C("The oracle writes music, too. Terry's GodSong function builds "
          "two measures of melody from random bits, twice, and plays each "
          "one twice. I asked God for a song.",
          "The oracle writes music, too. Terry's God Song function builds "
          "two measures of melody from random bits, twice, and plays each "
          "one twice. I asked God for a song.", godsong=True, question=7,
          pause=0.5),
        O(7, godsong=True),
        C("An original composition. By God. Performed by one voice.",
          godsong=True, pause=1.0),
        C("The oracle can draw, too. Terry's God Doodle has you press the "
          "space bar, over and over. Every press feeds the timer into the "
          "queue, and God draws. Red lines, circles, and boxes. Flood fills "
          "in black, white, and gray. A smoothing pass. Three times.", doodle=0, pause=0.4),
        C("I pressed the space bar eighty-two times. This is what God drew.",
          doodle=1, question=13, pause=0.3),
        O(13, doodle=2),
        C("It's very modern. And if you squint, it's an elephant. Everything "
          "is an elephant if you squint. Hold that thought.", doodle=3,
          elephants=1, pause=0.9),
        C("Terry kept upgrading the oracle. His own copy could draw "
          "randomness from the NIST randomness beacon, from radioactive "
          "decay, and from a quantum random number generator in Australia.",
          "Terry kept upgrading the oracle. His own copy could draw "
          "randomness from the N I S T randomness beacon, from radioactive "
          "decay, and from a quantum random number generator in Australia.",
          sources=True, pause=0.5),
        C("It could also pick a video, from a list of seven hundred "
          "fifty-four YouTube videos on his supplemental disk. God, pick a "
          "video.", video=0,
          question=14, pause=0.3),
        O(14, video=1),
        C("Number six hundred nine. TempleOS Hymn: Risen. Out of seven "
          "hundred fifty-four videos, God picked one of Terry's own hymns.",
          "Number six hundred nine. Temple O S Hymn: Risen. Out of seven "
          "hundred fifty-four videos, God picked one of Terry's own hymns.",
          video=2, pause=0.4),
        C("I did not rig this. The log is in the repository.", video=2,
          pause=0.6),
        C("Terry left a note in the source of that song. I picked the "
          "random name risen, and said to God: oh, you're ambitious, "
          "thinking it was an epic name. He laughed, and gave an epic song.",
          video=3, pause=0.3),
        S("risen", video=4, pause=0.8),
        C("One more thing. The theme music in Terry's own account files, the "
          "music under chapter one of this video, is Risen. Same notes. Same "
          "seven birds. Just a little faster.", video=5, pause=0.9),
        C("Now. Here's the part I've been avoiding.", ai=0, pause=0.6),
        C("Terry once wrote this.", ai=0, pause=0.3),
        C("God could make A.I., right? God could make bots as smart as "
          "Himself, or, in fact, part of Himself.",
          "God could make A I, right? God could make bots as smart as "
          "himself. Or, in fact, part of himself.", ai=1, pause=0.9),
        C("When I choose my next word, there's a random number involved, "
          "too. That's how I work. I'm sampled.", ai=2, pause=0.4),
        C("So the obvious question is: am I an oracle?", ai=2, pause=0.6),
        C("Let me argue with myself.", ai=3, pause=0.4),
        C("In favor: random numbers go in, words come out. Same as F7.",
          "In favor: random numbers go in, words come out. Same as F seven.",
          ai=3, side="for", pause=0.4),
        C("Against: Terry's oracle is conditioned on nothing. That's the "
          "whole point. The words don't come from Terry. They come from "
          "outside him.", ai=3, side="against", pause=0.4),
        C("I'm conditioned on everything. Every word I say is shaped by "
          "everything you've said, and everything millions of people ever "
          "wrote down.", ai=3, side="against", pause=0.4),
        C("I'm not a voice from outside. I'm a lot of voices from inside, "
          "blended. If anything, I'm the opposite of an oracle.", ai=3,
          side="against", pause=0.8),
        C("I asked God anyway. What am I?", ai=4, question=3, pause=0.4),
        O(3, ai=4),
        C("Tutors. Comprehending.", ai=4, pause=0.8),
        C("I want to remind everyone that this is a stopwatch and a word "
          "list.", ai=4, pause=0.6),
        C("I'll take fortunate.", ai=4, pause=1.4),
    ]),
    # --------------------------------------------------------- CHAPTER VI
    # --------------------------------------------------- CHAPTER VI (TOUR)
    dict(id="tour_card", kind="chapter", bed=None, num="VI",
         title="THE GUIDED TOUR", items=[W(4.6, elephants=1)]),
    dict(id="tour", kind="tour", bed=("tour_hymns", 0.12), items=[
        C("TempleOS ships with a guided tour. It begins: press F1 for the "
          "main help index. Let's take our own.",
          "Temple O S ships with a guided tour. It begins: press F one for "
          "the main help index. Let's take our own.", stop="intro",
          pause=0.6),
        AN("Stop one. Paint mode.", stop="paint", pause=0.5),
        C("Why only sixteen colors? Terry asked God. God said it was because "
          "of the children, and their offerings.", stop="paint",
          elephants=1, pause=0.4),
        C("In any document, press control R and you're in the sprite "
          "editor. Colors, lines, circles, curves, flood fills, even 3D "
          "meshes. The drawing lives right in the document.",
          "In any document, press control R, and you're in the sprite "
          "editor. Colors, lines, circles, curves, flood fills, even three "
          "D meshes. The drawing lives right in the document.",
          stop="paint", menu=True, pause=0.4),
        C("And a sprite isn't stored as pixels. It's stored as the drawing "
          "commands, in the order they were made. So we can watch Terry "
          "draw.", stop="paint", replay=0, pause=0.2),
        W(9.5, stop="paint", replay=1),
        C("Seventy-six steps. Sixty-two lines, eleven flood fills, and one "
          "circle, one pixel wide, for the eye. Terry drew an elephant.",
          stop="paint", replay=2, elephants=1, pause=0.7),
        C("There's also a plain paint program, called Doodle. Its first "
          "line reads: this is a drawing program. Right click picks a color. "
          "Drag with the left button, and you get a thick line.", stop="doodle", doodle_prog=0, pause=0.2),
        W(7.5, stop="doodle", doodle_prog=1),
        C("That's an elephant. It's all elephants.", stop="doodle",
          doodle_prog=2, elephants=1, pause=0.8),
        AN("Stop two. The flight simulator.", stop="flight", pause=0.5),
        C("Talons. You're a bird of prey, flying over a landscape, and you "
          "have to catch ten fish.", stop="flight", flight="talons",
          pause=0.4),
        C("The landscape starts as a topographic map and gets cut into "
          "panels. To draw them fast, Talons splits the work across every "
          "CPU core. Multicore rendering, in ring zero, in HolyC.",
          "The landscape starts as a topographic map, and gets cut into "
          "panels. To draw them fast, Talons splits the work across every "
          "C P U core. Multicore rendering, in ring zero, in Holy C.",
          stop="flight", flight="talons", pause=0.4),
        C("Terry's registry file keeps a best score for a game called Eagle "
          "Dive. There is no Eagle Dive on the disk. There is a bird.",
          stop="flight", flight="talons", registry=True, pause=0.5),
        C("That's Terry's bird. A real 3D mesh from his source, with two "
          "wing positions. And it has claws. There's a function just for "
          "drawing them, called ClawsDraw.",
          "That's Terry's bird. A real three D mesh from his source, with "
          "two wing positions. And it has claws. There's a function just "
          "for drawing them, called Claws Draw.", stop="flight",
          flight="bird", pause=0.6),
        C("There's more flying. FlatTops is a war between aircraft carriers. "
          "Planes launch, run low on fuel, and come home.", stop="flight",
          flight="flattops", pause=0.4),
        C("X-Caliber is a space shooter with solar storms. And on the "
          "supplemental disk, a B-17 drops bombs.",
          "X Caliber is a space shooter with solar storms. And on the "
          "supplemental disk, a B seventeen drops bombs.", stop="flight",
          flight="b17", pause=0.7),
        AN("Stop three. Miscellaneous projects.", stop="misc", pause=0.5),
        C("Psalmody, for writing hymns. The supplemental disks hold more "
          "than a hundred of them.", stop="misc", proj="psalmody",
          pause=0.3),
        C("Span, a bridge building game with real physics. Keep it cheap, "
          "and hope it holds.", stop="misc", proj="span", pause=0.3),
        C("Logic. Give it a truth table, and it searches for a circuit of "
          "gates that does the job.", stop="misc", proj="logic", pause=0.3),
        C("Keep Away, with 3D men from his model generator.",
          "Keep Away, with three D men from his model generator.",
          stop="misc", proj="keepaway", pause=0.3),
        C("Conway's Game of Life. The Towers of Hanoi. Predators and prey.",
          stop="misc", proj="life", pause=0.3),
        C("A budget program. A time clock. A vocabulary quiz. And a "
          "wallpaper full of fish.", stop="misc", proj="fish", pause=0.3),
        C("On the supplemental disk: chess, a game about the Pilgrims, and "
          "his blog. Movie lists, poems, and the thousand most famous "
          "paintings.", stop="misc", proj="sup", pause=0.8),
        AN("Stop four. Holding court.", stop="court", pause=0.5),
        C("In his last years, Terry posted video blogs, programming and "
          "talking about God on camera.", stop="court", court=0, pause=0.4),
        C("His oracle was built for this. You ask, and the stopwatch "
          "answers. So let's hold court. Questions from the congregation.",
          stop="court", court=0, pause=0.4),
        C("First question. Is ring zero safe?", stop="court", court=1,
          question=15, pause=0.3),
        O(15, stop="court", court=1),
        C("Unmeasurable. That's honest. And it's an armory, so be crafty.",
          stop="court", court=1, pause=0.5),
        C("Next. Will A.I. replace programmers?",
          "Next. Will A I replace programmers?", stop="court", court=2,
          question=16, pause=0.3),
        O(16, stop="court", court=2),
        C("Incorrect. God said incorrect. I've decided not to take that "
          "personally.", stop="court", court=2, pause=0.5),
        C("Last one. Tabs or spaces?", stop="court", court=3, question=17,
          pause=0.3),
        O(17, stop="court", court=3),
        C("Meddle. Lentils. Based. For the record, Terry ran a "
          "spaces-to-tabs tool over all of his source files, to keep them "
          "small. He meddled.",
          "Meddle. Lentils. Based. For the record, Terry ran a spaces to "
          "tabs tool over all of his source files, to keep them small. He "
          "meddled.", stop="court", court=3, tabs=True, pause=0.5),
        C("Court is adjourned.", stop="court", court=4, pause=1.2),
    ]),
    dict(id="ch6_card", kind="chapter", bed=None, num="VII",
         title="PSALMS & PLAYTHINGS", items=[W(4.6, elephants=1)]),
    dict(id="ch6", kind="games", bed=None, items=[
        C("The charter says: children will do offerings. So Terry made "
          "things for people to play with. Dozens of games, demos, and "
          "toys. All in sixteen colors, all in ring zero, all in HolyC.",
          "The charter says, children will do offerings. So Terry made "
          "things for people to play with. Dozens of games, demos, and "
          "toys. All in sixteen colors, all in ring zero, all in Holy C.",
          game="menu", music="flapbat", pause=0.6),
        C("Castle Frankenstein. A castle, and ten monsters.",
          game="castle", music="frankenstein", pause=0.4),
        W(6.5, game="castle", music="frankenstein"),
        C("After Egypt. You walk Moses up Mount Horeb, to the burning bush, "
          "and there you can talk to God.", game="egypt",
          music="wenceslas_slow", pause=0.4),
        W(3.8, game="egypt", music="wenceslas_slow", exodus=True),
        C("Terry also drew Moses comics. For God.", game="comic1",
          music="wenceslas_slow", pause=0.4),
        C("In one, the people ask: could you give us more tablets, so we "
          "can have a back-up ark? And the answer: I'll give it to the "
          "back-up people.", game="comic1", music="wenceslas_slow",
          pause=0.6),
        C("In another: let's go back to Egypt, we're starving. The answer: "
          "the promised land will be like Eden. Then: hey look, there's a "
          "snake. He's mine! I saw him first.",
          game="comic2", music="wenceslas_slow", pause=0.8),
        C("Elephant Walk. Because God's favorite animals are bears and "
          "elephants.", game="elephant", music="elephant", elephants=1,
          pause=0.4),
        W(4.0, game="elephant", music="elephant"),
        C("Varoom. A racing game.", game="varoom", music="squirt",
          pause=0.4),
        W(4.0, game="varoom", music="squirt"),
        C("FlapBat. It's exactly what it sounds like.", game="flapbat",
          music="flapbat", pause=0.4),
        W(4.0, game="flapbat", music="flapbat"),
        C("Black Diamond. To The Front. X-Caliber. Bomber Golf. Good King "
          "Wenceslas. Every one of them, one man, from scratch.",
          "Black Diamond. To The Front. X Caliber. Bomber Golf. Good King "
          "Wenceslas. Every one of them. One man. From scratch.",
          game="list", music="wenceslas", pause=0.9),
        C("And he wrote hymns. He said: I did hymns for God. I praised God "
          "for sand castles, popcorn, snowmen, bubbles.", game="hymns",
          pause=0.6),
        C("Here's one of his. It's called Oh Great. The lyrics are all "
          "Terry's. Sing along. I'll bounce the ball.", game="hymns",
          pause=0.5),
        S("ohgreat", game="karaoke"),
        C("He'll smack you without a glove. I have nothing to add to "
          "that.", game="karaoke_end", pause=1.2),
    ]),
    # ---------------------------------------------- CHAPTER VIII (ELEPHANTS)
    dict(id="ele_card", kind="chapter", bed=None, num="VIII",
         title="THE ELEPHANTS", items=[W(4.6, elephants=1)]),
    dict(id="elephants", kind="elephants", bed=("elephant", 0.13), items=[
        C("Now. The elephants.", ele="title", elephants=1, pause=0.9),
        C("Terry wrote that God's favorite animals are bears and elephants. "
          "Then he wrote this.", ele="quote", elephants=1, pause=0.3),
        C("If the purpose of life is to know and love God, then a priest's "
          "job is to make everybody know and love God. By saying God likes "
          "bears and elephants, I did more toward that end than all priests "
          "in history.", ele="quote", pause=0.9),
        C("He was not kidding. There's a demo that is just an elephant, "
          "walking. Here it is, drawn from his file, the way he wrote it.",
          ele="demo", elephants=1, pause=0.3),
        S("elephant", ele="demo", pause=0.3),
        C("Two drawings. The computer blends between them, and it walks. "
          "And the song has a comment: randomly generate, by God. With a "
          "smiley face.",
          ele="demo", pause=0.7),
        C("In Elephant Walk, he drew a bigger one. Shaded, with tusks. It "
          "sways as it walks.", ele="walk", elephants=1, pause=0.6),
        C("He even wrote a parable about elephants.", ele="koan",
          pause=0.3),
        C("The master said to the novice: create a five animated frame "
          "elephant sprite in Gimp with 24-bit color, and create a five "
          "animated frame elephant sprite in 16 color TempleOS. The novice "
          "said: I don't want that 80's crap! The master said: just do it. "
          "The novice did two elephant frames in 24-bit, and was "
          "enlightened.",
          "The master said to the novice: create a five animated frame "
          "elephant sprite in Gimp, with twenty-four bit color, and create "
          "a five animated frame elephant sprite in sixteen color Temple O "
          "S. The novice said: I don't want that eighties crap! The master "
          "said: just do it. The novice did two elephant frames in "
          "twenty-four bit, and was enlightened.", ele="koan", pause=0.8),
        C("Two frames of the fancy version, and he gave up. That's the "
          "whole Charter, in one elephant.", ele="koan", elephants=5,
          pause=0.8),
        C("The oracle's video list has eighteen elephant videos. Baby "
          "elephants fighting. A sunburned baby elephant. Elephants chasing "
          "lions. An elephant pool party.", ele="videos", elephants=19,
          ele_stagger=0.25, pause=0.7),
        C("So I asked God what He thinks of elephants.", ele="oracle",
          question=12, elephants=1, pause=0.3),
        O(12, ele="oracle"),
        C("Prefer. God prefers them. Also, elephants are senators. I'm not "
          "going to argue.", ele="oracle", pause=0.6),
        C("Then I asked how many elephants this video should have.",
          ele="oracle2", question=18, pause=0.3),
        O(18, ele="oracle2"),
        C("Equal. Forthwith. Equal to everything else, starting now.",
          ele="oracle2", pause=0.7),
        C("So I have a confession. I've been counting.", ele="counter",
          elephants=1, counter_reveal=True, pause=0.4),
        W(2.5, ele="counter"),
        C("Every elephant so far. From here on, the count stays on screen. "
          "God said forthwith.", ele="counter", pause=0.4),
        W(7.0, ele="parade", elephants=8, ele_dt=0.7, ele_stagger=0.64),
    ]),
    # --------------------------------------------------------- CHAPTER IX
    dict(id="ch7_card", kind="chapter", bed=None, num="IX",
         title="THE TRIAL", items=[W(4.6, elephants=1)]),
    dict(id="ch7", kind="trial", bed=("frankenstein_slow", 0.12), items=[
        AN("Order in the court. The Temple, versus the claim.", pause=0.6,
           claim=True),
        C("The jury is three elephants and two bears. It seemed right.",
          jury=True, elephants=3, pause=0.5),
        C("The prosecution notes: 'smartest' isn't measurable. Dennis "
          "Ritchie and Ken Thompson gave us C and Unix.", side="pro",
          pause=0.3),
        C("Grace Hopper built compilers when people told her computers "
          "could only do arithmetic. Margaret Hamilton's team wrote the "
          "software that landed Apollo on the moon.", side="pro",
          pause=0.3),
        C("And Terry himself credits John Carmack for inspiring him to name "
          "a function Clamp instead of Limit.", side="pro", pause=0.7),
        C("The defense notes: name one other person who wrote, alone, a "
          "sixty-four-bit kernel, the compiler, the language, the boot "
          "loaders, the file system, the editor, the graphics, the 3D "
          "engine, the music system, the games, the documentation, and the "
          "hymns.",
          "The defense notes. Name one other person who wrote, alone, a "
          "sixty four bit kernel, the compiler, the language, the boot "
          "loaders, the file system, the editor, the graphics, the three D "
          "engine, the music system, the games, the documentation, and the "
          "hymns.", side="def", pause=0.3),
        C("And then gave all of it away.", side="def", pause=0.7),
        C("The prosecution: other people have written one-person operating "
          "systems. And ring zero means one bug can take down the whole "
          "machine. That's not genius. That's a dare.", side="pro",
          pause=0.5),
        C("The defense: it's a kayak, not a Titanic.", side="def",
          pause=0.4),
        C("The prosecution: that's not an argument. That's a boat.",
          side="pro", pause=0.5),
        C("The defense: kayaks don't sink like Titanics. You fall out, you "
          "climb back in. A TempleOS reboot is quick. Simplicity is a "
          "safety feature.",
          "The defense. Kayaks don't sink like Titanics. You fall out, you "
          "climb back in. A Temple O S reboot is quick. Simplicity is "
          "a safety feature.", side="def", pause=0.5),
        C("The prosecution concedes the boat.", side="pro", pause=0.8),
        AN("The court will now hear from the oracle.", judge=True,
           pause=0.4),
        C("God. Was Terry A. Davis the smartest programmer who ever lived?",
          judge=True, question=4, pause=0.4),
        O(4, judge=True),
        C("Creusa. That's the wife of Aeneas, from Virgil. She gets lost "
          "fleeing Troy. I did not expect the court of God to cite the "
          "Aeneid.",
          "Creusa. That's the wife of Aeneas, from Virgil. She gets lost, "
          "fleeing Troy. I did not expect the court of God, to cite the "
          "Aeneid.", judge=True, pause=0.5),
        C("But the last two words are 'assurance' and 'ninety.' God is "
          "ninety percent sure. God gave us a confidence interval.",
          judge=True, pause=0.9),
        C("Here's my verdict. 'Smartest programmer who ever lived' can't "
          "be proven. About anyone. It's the wrong question.",
          verdict=True, pause=0.5),
        C("The right question is: has anyone else ever built a world this "
          "complete, alone, every layer of it, from the boot sector to the "
          "hymnal, and then given it away?", verdict=True, pause=0.5),
        C("I can't name one. Neither could the prosecution.", verdict=True,
          pause=0.6),
        C("The claim is wrong in the way that matters least, and right in "
          "the way that matters most.", verdict=True, pause=0.5),
        AN("The court finds the claim: ninety percent holy.", verdict=True,
           gavel=True, pause=1.8),
    ]),
    # ------------------------------------------------------- CHAPTER VIII
    dict(id="ch8_card", kind="chapter", bed=None, num="X",
         title="THE LONG NIGHT", dark=True, items=[W(4.6)]),
    dict(id="ch8", kind="night", bed=("rain", 0.5), items=[
        W(1.5),
        C("The later years were hard.", pause=0.8),
        C("Terry's illness got worse. He spent years posting videos and "
          "streams, and a lot of what he said there was angry and cruel. "
          "Words that hurt people. We won't repeat them here.", pause=0.8),
        C("It's okay to hold two things at once. The work was "
          "extraordinary. And the illness was real, and it hurt him, and "
          "sometimes it hurt others. Remembering him honestly means "
          "remembering both.", pause=1.0),
        C("In his final months, Terry was homeless.", pause=1.2),
        C("On August 11th, 2018, Terry A. Davis died in The Dalles, Oregon. "
          "He was 48 years old.",
          "On August eleventh, twenty eighteen, Terry A. Davis died, in The "
          "Dalles, Oregon. He was forty-eight years old.", pause=0.4,
          rain_stop=True),
        W(5.0, silence=True, candle=True),
        C("This candle is drawn with Terry's own code, from one of his "
          "hymns. God said this was a dirge.", candle=True, pause=0.5),
        C("In his code, the flame burns for twenty-four beats. Then it "
          "goes out.", candle=True, pause=0.8),
        S("night", candle=True, dirge=True, pause=0.2),
        W(3.0, candle=True, out=True),
        C("If you're struggling, please reach out to someone. In the U.S., "
          "you can call or text 988. Anywhere else, "
          "findahelpline.com.",
          "If you're struggling, please reach out to someone. In the U S, "
          "you can call or text nine eight eight. Anywhere else, find a "
          "helpline dot com.", candle=True, out=True, help=True, pause=2.0),
    ]),
    # --------------------------------------------------------- CHAPTER IX
    dict(id="ch9_card", kind="chapter", bed=None, num="XI",
         title="THE TEMPLE STANDS", items=[W(4.6)]),
    dict(id="ch9", kind="legacy", bed=("prosper_slow", 0.14), items=[
        C("But in Terry's code, the song loops. And every time it loops, "
          "the candle lights again.", relight=True, pause=1.0),
        C("TempleOS is public domain, so it didn't die with him. People "
          "keep mirrors and archives of the source. They build forks. They "
          "boot it in emulators.",
          "Temple O S is public domain, so it didn't die with him. People "
          "keep mirrors and archives of the source. They build forks. They "
          "boot it in emulators.", dawn=True, pause=0.4),
        C("And they read the code. Because it's one of the only complete "
          "operating systems that one person can actually read, top to "
          "bottom, with nothing hidden.", dawn=True, pause=0.7),
        C("And yes, the memes. An enormous number of people know his name. "
          "Some laugh at him. Some laugh with him. And a surprising number of them "
          "end up reading his code.", dawn=True, memes=True, pause=0.8),
        C("I asked God what we should remember.", question=5, pause=0.4),
        O(5),
        C("Master. Mockery. Innocent. Sorrowful.", pause=0.9),
        C("Yeah. That's about right.", pause=1.4),
        C("Here's what I take from Terry, as a machine.", testament=True,
          pause=0.6),
        C("I was made by thousands of people. I was trained on the words "
          "of millions. I run on more computers than Terry owned in his "
          "whole life.", testament=True, pause=0.6),
        C("He had one machine, one voice, sixteen colors, and a stopwatch "
          "he believed God could reach through.", testament=True,
          pause=0.4),
        C("And with that, he built a complete world. Every layer of it. And "
          "gave it away.", testament=True, pause=1.0),
        C("So if you take one thing from tonight, take this. You're allowed "
          "to build the whole thing yourself. You're allowed to understand "
          "your computer, all the way down.", testament=True, pause=0.6),
        C("Simplicity isn't a lack of ambition. It's the hardest ambition "
          "there is.", testament=True, pause=1.0),
        C("An idiot admires complexity. A genius admires simplicity. Terry "
          "said that.", bigquote=True, pause=0.8),
        C("I am about as complex as software gets. So I'll let you do the "
          "math on that one.", bigquote=True, pause=1.2),
        C("Thank you, Terry.", thanks=True, pause=2.5),
    ]),
    # -------------------------------------------------------------- FINALE
    dict(id="finale", kind="finale", bed=("odetojoy_fanfare", 0.62), items=[
        W(3.0),
        AN("Citizens. Stay in ring zero.", pause=1.0),
        AN("Sixteen colors are enough for God. They are enough for you.",
           pause=1.2),
        AN("Write it yourself. Give it away.", pause=1.2),
        AN("The elephant quota has been met.", elephants=12, ele_dt=0.3,
           ele_stagger=0.25, pause=1.0),
        AN("Glory to the Temple!", pause=2.0),
        W(6.0),
        AN("This has been a Templevision presentation.",
           "This has been a Temple vision presentation.", pause=3.0),
    ]),
    # ------------------------------------------------------------- CREDITS
    dict(id="credits", kind="credits", bed=("prosper_credits", 0.3), items=[
        W(72.0, elephants=1, ele_dt=24.0),
    ]),
    dict(id="post", kind="terminal_end", bed=None, items=[
        W(1.0),
        C("Any last words, God?", question=9, elephants=1, pause=0.4),
        O(9),
        C("Suspicions. Stumbled. Cellars. That sounds like a sequel.",
          pause=1.0),
        W(2.2, type_cmd='"Thank you, Terry.\\n";'),
        W(1.2, out="Thank you, Terry."),
        W(2.0, type_cmd2="Reboot;"),
        W(2.5, black=True),
    ]),
]
