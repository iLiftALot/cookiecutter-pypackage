from dataclasses import Field, dataclass, field
from dataclasses import fields as dc_fields
from typing import Any, ClassVar, Literal, dataclass_transform

type TkFontDescription = tuple[
    str,
    int,
    Literal["normal", "bold"],
    Literal["roman", "italic"],
    Literal["normal", "underline"],
    Literal["normal", "overstrike"],
]

type TkNamedFont = Literal[
    "TkDefaultFont",
    "TkTextFont",
    "TkFixedFont",
    "TkMenuFont",
    "TkHeadingFont",
    "TkCaptionFont",
    "TkSmallCaptionFont",
    "TkIconFont",
    "TkTooltipFont",
]

type TkFontFamily = Literal[
    "Academy Engraved LET",
    "Al Bayan",
    "Al Nile",
    "Al Tarikh",
    "American Typewriter",
    "Andale Mono",
    "Apple Braille",
    "Apple Chancery",
    "Apple Color Emoji",
    "Apple SD Gothic Neo",
    "Apple Symbols",
    "AppleGothic",
    "AppleMyungjo",
    "Arial",
    "Arial Black",
    "Arial Hebrew",
    "Arial Hebrew Scholar",
    "Arial Narrow",
    "Arial Rounded MT Bold",
    "Arial Unicode MS",
    "Avenir",
    "Avenir Next",
    "Avenir Next Condensed",
    "Ayuthaya",
    "Baghdad",
    "Bangla MN",
    "Bangla Sangam MN",
    "Baskerville",
    "Beirut",
    "Big Caslon",
    "Bodoni 72",
    "Bodoni 72 Oldstyle",
    "Bodoni 72 Smallcaps",
    "Bodoni Ornaments",
    "Bradley Hand",
    "Brush Script MT",
    "Chalkboard",
    "Chalkboard SE",
    "Chalkduster",
    "Charter",
    "Cochin",
    "Comic Sans MS",
    "Copperplate",
    "Corsiva Hebrew",
    "Courier New",
    "DIN Alternate",
    "DIN Condensed",
    "Damascus",
    "DecoType Naskh",
    "Devanagari MT",
    "Devanagari Sangam MN",
    "Didot",
    "Diwan Kufi",
    "Diwan Thuluth",
    "Euphemia UCAS",
    "Farah",
    "Farisi",
    "Futura",
    "GB18030 Bitmap",
    "Galvji",
    "Geeza Pro",
    "Georgia",
    "Gill Sans",
    "Grantha Sangam MN",
    "Gujarati MT",
    "Gujarati Sangam MN",
    "Gurmukhi MN",
    "Gurmukhi MT",
    "Gurmukhi Sangam MN",
    "Heiti SC",
    "Heiti TC",
    "Helvetica",
    "Helvetica Neue",
    "Herculanum",
    "Hiragino Maru Gothic ProN",
    "Hiragino Mincho ProN",
    "Hiragino Sans",
    "Hiragino Sans GB",
    "Hoefler Text",
    "ITF Devanagari",
    "ITF Devanagari Marathi",
    "Impact",
    "InaiMathi",
    "Kailasa",
    "Kannada MN",
    "Kannada Sangam MN",
    "Kefa III",
    "Khmer MN",
    "Khmer Sangam MN",
    "Kohinoor Bangla",
    "Kohinoor Devanagari",
    "Kohinoor Gujarati",
    "Kohinoor Telugu",
    "Kokonor",
    "Krungthep",
    "KufiStandardGK",
    "Lao MN",
    "Lao Sangam MN",
    "Lucida Grande",
    "Luminari",
    "Malayalam MN",
    "Malayalam Sangam MN",
    "Marker Felt",
    "Menlo",
    "MesloLGS NF",
    "Microsoft Sans Serif",
    "Mishafi",
    "Mishafi Gold",
    "Monaco",
    "Mshtakan",
    "Mukta Mahee",
    "Muna",
    "Myanmar MN",
    "Myanmar Sangam MN",
    "Nadeem",
    "New Peninim MT",
    "Noteworthy",
    "Noto Nastaliq Urdu",
    "Noto Sans Batak",
    "Noto Sans Kannada",
    "Noto Sans Myanmar",
    "Noto Sans NKo",
    "Noto Sans Oriya",
    "Noto Sans Syriac",
    "Noto Sans Tagalog",
    "Noto Serif Myanmar",
    "Optima",
    "Oriya MN",
    "Oriya Sangam MN",
    "PT Mono",
    "PT Sans",
    "PT Sans Caption",
    "PT Sans Narrow",
    "PT Serif",
    "PT Serif Caption",
    "Palatino",
    "Papyrus",
    "Party LET",
    "Phosphate",
    "PingFang HK",
    "PingFang MO",
    "PingFang SC",
    "PingFang TC",
    "Plantagenet Cherokee",
    "Raanana",
    "Rockwell",
    "STIX Two Math",
    "STIX Two Text",
    "STSong",
    "Sana",
    "Sathu",
    "Savoye LET",
    "Shree Devanagari 714",
    "SignPainter",
    "Silom",
    "Sinhala MN",
    "Sinhala Sangam MN",
    "Skia",
    "Snell Roundhand",
    "Songti SC",
    "Songti TC",
    "Sukhumvit Set",
    "Symbol",
    "Tahoma",
    "Tamil MN",
    "Tamil Sangam MN",
    "Telugu MN",
    "Telugu Sangam MN",
    "Thonburi",
    "Times New Roman",
    "Trattatello",
    "Trebuchet MS",
    "Verdana",
    "Waseem",
    "Webdings",
    "Wingdings",
    "Wingdings 2",
    "Wingdings 3",
    "Zapf Dingbats",
    "Zapfino",
]
type FontSpec = TkNamedFont | TkFontFamily | str


@dataclass_transform(field_specifiers=(field,))
class TkFontMeta(type):
    def __new__(mcs, name, bases, ns, **kwds):
        value = property(
            lambda self: (
                self.family,
                self.size,
                self.weight,
                self.slant,
                self.underline,
                self.overstrike,
            )
        )
        fields = property(lambda self: dc_fields(self))
        ns["value"] = value
        ns["fields"] = fields
        return super().__new__(mcs, name, bases, ns, **kwds)

    def __init__(cls, name, bases, ns, **kwds):
        super().__init__(name, bases, ns, **kwds)
        if any(b.__name__ == "TkFontBase" for b in bases):
            dataclass(cls)


class TkFontBase(metaclass=TkFontMeta):
    """
    Base class for TkFont.

    Used to support dataclass_transform and type checking.
    """

    value: ClassVar[TkFontDescription]
    fields: ClassVar[dict[str, Field[Any]]]


class TkFont(TkFontBase):
    """Font specification for label fields.

    Parameters:
        family: Font family name, e.g. ``"Arial"``.
        size: Font size in points.
        weight: Font weight, e.g. ``"bold"``, ``"normal"``.
        slant: Font slant, e.g. ``"roman"``, ``"italic"``.
        underline: Whether the font is underlined.
        overstrike: Whether the font is overstruck.
    """

    family: FontSpec = field(default="TkDefaultFont")
    size: int = field(default=12)
    weight: Literal["normal", "bold"] = field(default="normal")
    slant: Literal["roman", "italic"] = field(default="roman")
    underline: Literal["normal", "underline"] = field(default="normal")
    overstrike: Literal["normal", "overstrike"] = field(default="normal")
