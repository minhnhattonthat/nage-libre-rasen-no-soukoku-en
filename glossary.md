# Glossary - Nage Libre: Rasen no Soukoku

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables: a JP term in a line needs its EN form (one-kanji names only when the
line gives their furigana or an honorific), and an Avoid spelling fails.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Ann-chan, Makoto-san, Kurosawa-senpai). Name order: Western (given name first).
- Romanisation source: official English names where they exist (none known), else an earlier fan patch (none
  known), else Hepburn without macrons (Kiryu, Ryo, Daido). Exception: 杏 = Ann (あん; "An" reads as the article).
- Credits: English.
- Register / flavour: light comedy RPG about five high-school girls; casual, bubbly teen speech among the girls,
  rougher talk from delinquents and monsters, polite speech where the JP is polite (Mio). Natural modern
  English, contractions, no archaic or stiff textbook phrasing. Sound effects: English onomatopoeia (にゃ～ ->
  "Meow~"), keep the JP's length and repetition.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening. Stat names stay the
  game's two-letter forms (HP, AT, MT, DF, AG) because the JP uses them too.

## Style rules
- Punctuation map: 「」 -> "...", 『』 and ”...” (item/term quotes) -> "...", ・・・ -> ..., ！？ -> ?!, ～ at a word
  end -> ~ (a drawn-out sound; `~` is in the font), ー stretching a word -> repeat a letter ("Noooo") or ~.
- No `\` and no bare `%` (the renderer reads `%` as a control code). Copy `%c02`-style colour codes exactly.
- Drop furigana: 樹%h（いつき）%z -> Itsuki. Drop %h/%z everywhere (half-width switch, English is half-width).
- Dialogue: write the box as one utterance; the build wraps by pixel width and pages long lines. No `\n` in
  dialogue except where the JP lays out a list or a title (clear-condition boxes, signs).
- Voices: docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 杏 | Ann | | Ann Akagi (赤城 杏), lead heroine, face 1. Energetic, blunt, leader type | |
| 樹 | Itsuki | | Itsuki Morino (森野 樹), face 2. Casual, lazy, boy-crazy | |
| 真 | Makoto | | Makoto Matsunaga (松永 真), face 3 | |
| 忍 | Shinobu | | Shinobu Kazama (風間 忍), face 4 | |
| 澪 | Mio | | Mio Tsukushi (筑紫 澪), face 5 | |
| 迅 | Jin | | Jin Kiryu (桐生 迅) | |
| 大 | Dai | | Dai Wajima (輪島 大) | |
| 赤城 | Akagi | | Ann's surname | |
| 森野 | Morino | | | |
| 松永 | Matsunaga | | | |
| 風間 | Kazama | | | |
| 筑紫 | Tsukushi | | | |
| 桐生 | Kiryu | | | Kiryuu |
| 輪島 | Wajima | | | |
| 司 | Tsukasa | | つかさ | |
| 黒沢 | Kurosawa | | Ryo Kurosawa (黒沢 亮) | |
| 亮 | Ryo | | | Ryou |
| 神崎 | Kanzaki | | Kaoru Kanzaki (神崎 薫) | |
| 薫 | Kaoru | | | |
| 相田 | Aida | | Tsukasa Aida (相田 司), Nanju High council president | |
| 黒沢様 | Kurosawa-sama | | his followers; Lord Kurosawa also passes the check | |
| ブタくん | Pig-kun | | the pig monster's name label; ブタさん = Pig-san (honorifics on nouns used as names are kept) | Mr. Pig, Mister Pig |
| 雪だるまさん | Snowman-san | | MAP30, addressed by the girls | Mister Snowman |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 南寿高校 | Nanju High | | the girls' school | |
| 梅林学園 | Bairin Academy | | ばいりん | |
| 梅林 | Bairin | | | |
| 桜花高校 | Oka High | | おうか | Ouka |
| 大堂高校 | Daido High | | | Daidou |
| 英光学園 | Eiko Academy | | | Eikou |
| 商店街 | shopping street | | | |
| 南寿町 | Nanju Town | | | |
| 浮遊大陸 | Floating Continent | | | |
| 飛行戦艦 | flying battleship | | also 飛空戦艦 | |
| 大木 | Great Tree | | MAP14/MAP81 route name, Title Case with 滝 = Waterfall ("Great Tree" route); NAME/467 大木 is the surname Oki | Big Tree, big tree |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ナージュ像 | Nage Statue | | the stolen statue that kept monsters away | Naju |
| ナージュリーブル | Nage Libre | | game title (save data name) | |
| ナージュ | Nage | | | Naju, Nāju |
| 魔物 | monster | | also 化物, モンスター: monster | |
| 部活 | club | | after-school club = the job class system | |
| 生徒会長 | student council president | | | |
| 生徒会 | student council | | | |
| 帰宅部 | Go-Home Club | | no club; スーパー帰宅部 = Super Go-Home Club | |
| 着せかえ | dress-up | | between-stage outfit screen | |
| 誕生石 | birthstone | | 誕生石効果 = birthstone bonus | |
| ランダマカード | Randoma Card | | | |
| ランダマ | Randoma | | 超ランダマ = Super Randoma | |
| コビーロ | Kobiro | | battle command (magic) | |
| おやつ | snack | | battle/map command: heal a nearby ally | |
| クリアー条件 | Clear Condition | | stage goal box | |
| リセットボタン | Reset button | | | |
| アイテム | item | | | |
| コバク | Small Cracker | | 爆竹 = firecracker | |
| チューバク | Medium Cracker | | | |
| ダイバク | Big Cracker | | | |
| コボム | Small Bomb | | | |
| チューボム | Medium Bomb | | | |
| ダイボム | Big Bomb | | | |
| あめだま | Candy | | Ｓ/Ｍ/Ｌあめだま = S Candy, M Candy, L Candy | |
| ポテチ | Chips | | Ｓ/Ｍ/Ｌポテチ = S Chips, M Chips, L Chips | |
| すごいビタミン | Super Vitamin | | ビタミンＡＴ．Ｓ = Vitamin AT-S (also MT/DF/AG, .S/.L) | |
| スッキリン | Refreshin | | cures status ailments | |
| ピコハン | Squeaky Hammer | | | |
| アイアンタッブ | Iron Tub | | | |
| ペチャペチャ | Pie Splat | | | |
| バケビショ | Bucket Soak | | | |
| パフパフ | Puff Puff | | | |
| クラックダウン | Crackdown | | | |
| ナイトメア | Nightmare | | | |
| バブリン | Bubblin | | | |
| メテメテ | Meteo Meteo | | | |
| ザバザバ | Splish Splash | | | |
| レイレイ | Ray Ray | | | |
| グラグラ | Rumble Rumble | | | |
| ヒエヒエ | Chill Chill | | ヒエ family: Chill | |
| ゴツヒエ | Big Chill | | | |
| チョヒエ | Mega Chill | | | |
| ピカゴロ | Flash Boom | | | |
| ゴツピカ | Big Flash | | | |
| チョピカ | Mega Flash | | | |
| グルグル | Whirl Whirl | | | |
| チョグル | Mega Whirl | | | |
| マッタ | Time Out | | | |
| チョマタ | Mega Time Out | | | |
| サモンスター | Summon Star | | | |
| サモンホイホイ | Summon Shoo | | | |
| サモンオヤヂ | Summon Geezer | | | |
| サモンフレイム | Summon Flame | | | |
| アタプラ | AT Plus | | stat buffs: AT/MT/DF/AG Plus, Minus | |
| プワゾ | Poizon | | | |
| ギュギューン | Bzzzt | | paralysis | |
| チビＴ | Baby Tee | | clothing | |
| スカーフ | Scarf | | clothing names: Title Case, one form each | |
| ジーパン | Jeans | | | |
| ロングブーツ | Long Boots | | | |
| ローファー | Loafers | | | |
| ジャンパースカート | Jumper Skirt | | | |
| デニムショートパンツ | Denim Shorts | | | |
| モヘアニットセーター | Mohair Knit Sweater | | | |
| タンクトップ | Tank Top | | | |
| ダブルのジャケット | Double-Breasted Jacket | | | |
| ビキニのパンツ | Bikini Bottoms | | | |
| ビキニのブラ | Bikini Top | | | |
| リストバンド | Wristband | | | |
| 雪だるまのしおり | Snowman Bookmark | | | |
| ブルマー | bloomers | | gym bloomers; in item names Title Case: 2nd-Year Bloomers | |
| 魔導書 | spellbook | | "Got a spellbook." | grimoire |
| 怪鳥 | giant bird | | | monstrous bird |
| 着せかえ用アイテム | (dress-up item) | | after the get line: Got the "X". (dress-up item) | Item for dress-up |
| スーパー生徒 | Super Student | | | |
| 創造神 | Creator God | | 創造神ナージュ = the Creator God Nage | |
| 神崎グループ | Kanzaki Group | | | |
| 水泳部 | Swim Club | | club = 部; symbol line: Got the Swim Club symbol. | |
| 空手部 | Karate Club | | | |
| 弓道部 | Archery Club | | | |
| バレー部 | Volleyball Club | | also バレーボール部 | |
| 陸上部 | Track Club | | | |
| 調理部 | Cooking Club | | | |
| 手芸部 | Handicraft Club | | | Handicrafts |
| 軽音楽部 | Light Music Club | | | |
| 腕時計 | Wristwatch | | clothing / accessories, Title Case | |
| ステンレスチェーン | Stainless Chain | | | |
| 水色のジャケット | Light Blue Jacket | | | |
| 高級なバッグ | Designer Bag | | | Luxury Bag |
| 麻のジャケット | Linen Jacket | | | |
| 麻のフレアーパンツ | Linen Flared Pants | | | Flare Pants |
| ライダーズジャケット | Biker Jacket | | | Rider's Jacket |
| ジージャン | Denim Jacket | | | |
| 体操服 | Gym Uniform | | 一年生の体操服 = 1st-Year Gym Uniform | Gym Clothes |
| デニムスカート | Denim Skirt | | | |
| デニムベスト | Denim Vest | | | |
| ダウンベスト | Down Vest | | | |
| オーバーオール | Overalls | | | |
| ミニスカート | Miniskirt | | | |
| サングラス | Sunglasses | | | |
| タートルネックセーター | Turtleneck Sweater | | | |
| デッキシューズ | Deck Shoes | | | |
| レザーパンツ | Leather Pants | | | |
| ハイテクスニーカー | High-Tech Sneakers | | | |
| キャンバススニーカー | Canvas Sneakers | | | |
| トレッキングシューズ | Trekking Shoes | | | |
| エンジニアブーツ | Engineer Boots | | | |
| サンダル | Sandals | | | |

## Decisions from earlier batches
- (pilot) MAP86/MAP85 intro and MAP01 by the controller: docs/style-reference.md.
- b020 battle menu: たいき Wait, こうげき Attack, コビーロ Kobiro, おやつ Snack, とくしゅ Special, アイテム Item,
  そのた Other, ねむる Sleep, でんわ Phone, きがえ Dress. 特殊技 Special Skill, スペシャル攻撃 Special Attack, 通常攻撃
  Normal attack, 詰め合わせ Pack ("M Chips Pack"). Classes: 一般生徒 Regular Student, ドラゴン Dragon, ブタ Pig,
  ハネ Bat, 半魚人 Fishman. Club records (CLUB/nn) drop "Club": Swim, Karate, Archery, ...
- b021 description tags: ／単 /1, ／全 /All, ／前 /Front, ／後 /Back, ／体 /Phys, ／文 /Mind (guess: may be the
  athletic/culture club types; check in phase 8).
- b022 names: Hepburn per kanji reading guess (no furigana); モンスターA-I = Monster A-I.
- 黒沢様 = Kurosawa-sama, 神崎様 = Kanzaki-sama, 薫様 = Kaoru-sama (followers); 会長 alone = the president.
- ・・ with two dots = "..." in English unless the JP pause is mid-word.
