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
  rougher talk from delinquents and monsters, polite speech where the JP is polite (Itsuki). Natural modern
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
| ブルマー | bloomers | | gym bloomers | |

## Decisions from earlier batches
- (pilot) MAP86/MAP85 intro and MAP01 by the controller: docs/style-reference.md.
