// template.typ — entry point. Reads content.yaml via --input content=<path>
// (must be invoked with --root / so an absolute path resolves — see
// SKILL.md) and composes components.typ against it.

#import "components.typ": geo, sidebar-band, section-heading, bullet-list, job-entry, edu-entry, sidebar-block, nbh

#let content-path = sys.inputs.at("content")
#let data = yaml(content-path)

// Per-content page margins, in points, from an optional `layout:` block in
// the content file. Absent, the renderer's calibrated defaults apply, so
// the fidelity fixture and every version without the block render exactly
// as before. Only the top and bottom can be set: the left margin and the
// sidebar geometry are absolute-page values calibrated together.
#let layout = data.at("layout", default: (:))
#let margin-top = if "margin-top" in layout { layout.at("margin-top") * 1pt } else { geo.margin-top }
#let margin-bottom = if "margin-bottom" in layout { layout.at("margin-bottom") * 1pt } else { geo.margin-bottom }

#set page(
  width: geo.page-width,
  height: geo.page-height,
  margin: (top: margin-top, bottom: margin-bottom, left: geo.margin-left, right: 0pt),
  background: sidebar-band(),
)

#set text(font: "Lato", weight: 400, size: 9pt, fill: geo.ink)
// Typst's default block/paragraph spacing (~1.2em, scaled to whichever
// text size is active) would otherwise stack on top of every explicit
// #v() gap below, growing with each heading's font size. Zeroing it here
// makes #v() the sole source of vertical rhythm in the main column,
// matching the pattern bullet-list already uses locally for its list par.
#set block(spacing: 0pt)
#set par(spacing: 0pt)

// Placed here — before any main-column content that could overflow to a
// later page — because #place() binds to whichever page is "current" in
// the flow at the point it's called, not to page 1 unconditionally. Placing
// it after the (potentially overflowing) main column would anchor it to
// whatever page that content lands on. It doesn't consume flow space, so
// this position doesn't affect the name/subtitle layout below.
//
// Coordinate frame: this #place() sits in normal document flow, where
// `page(margin: ...)` is in effect, so dx/dy offset from the *margin
// content box* (top-left at absolute page (margin-left, margin-top)), not
// from the true page edge like `sidebar-band()`'s background placement
// does. `geo.sidebar-x`/`geo.sidebar-top` are absolute-page-edge values
// (from design-spec.md), so the margins the content box already adds are
// subtracted back out here to land at the intended absolute position.
// `box`'s width is a magnitude, not a position, so it's unaffected by the
// coordinate frame — it's still just "page-width minus the box's absolute
// left edge", i.e. the box's right edge lands exactly on the true page
// edge, matching the navy band.
//
// Paint order: because this #place() comes before the main-column block
// below, it paints first — the main column would paint over it if the two
// ever overlapped. That's safe only because the main column is
// width-constrained to `geo.col-width` (403.28pt sidebar-x, comfortably
// past by col-width's right edge at margin-left + col-width = 371.28pt);
// don't reorder these two or widen col-width past the sidebar without
// re-checking for overlap.
#place(top + left,
  dx: geo.sidebar-x + geo.sidebar-pad-left - geo.margin-left,
  dy: geo.sidebar-top - margin-top,
)[
  #box(width: geo.page-width - geo.sidebar-x - geo.sidebar-pad-left)[
    #sidebar-block("details", "Details", data.at("details", default: ()))
    #v(if data.at("details", default: ()).len() > 0 { geo.sb-rhythm.details.at(2) } else { 0pt })
    #sidebar-block("links", "Links", data.at("links", default: ()))
    #v(if data.at("links", default: ()).len() > 0 { geo.sb-rhythm.links.at(2) } else { 0pt })
    #sidebar-block("skills", "Skills", data.at("skills", default: ()))
    #v(if data.at("skills", default: ()).len() > 0 { geo.sb-rhythm.skills.at(2) } else { 0pt })
    #sidebar-block("hobbies", "Hobbies", data.at("hobbies", default: ()))
  ]
]

#block(width: geo.col-width)[
  #v(geo.pad-top)
  #text(font: "Oswald", weight: 500, size: geo.name-size, fill: black)[#data.name]
  #v(geo.gap-name-subtitle)
  #text(size: geo.subtitle-size)[#upper(data.title)]

  #let summary = data.at("summary", default: "")
  #if summary != "" [
    #v(geo.gap-subtitle-section)
    #section-heading("Professional Summary")
    #v(geo.gap-section-summary)
    #par(leading: geo.body-leading - geo.body-line-const)[#text(size: geo.body-size)[#nbh(summary)]]
  ]

  #if data.at("experience", default: ()).len() > 0 [
    #v(if summary != "" { geo.gap-summary-section } else { geo.gap-subtitle-section })
    #section-heading("Employment History")
    #for (i, job) in data.at("experience", default: ()).enumerate() [
      #v(if i == 0 { geo.gap-section-job } else { geo.gap-bullets-job })
      #job-entry(job)
    ]
  ]

  #if data.at("education", default: ()).len() > 0 [
    #v(geo.gap-bullets-section)
    #section-heading("Education")
    #for (i, edu) in data.at("education", default: ()).enumerate() [
      #v(if i == 0 { geo.gap-section-edu } else { geo.gap-edu-edu })
      #edu-entry(edu)
    ]
  ]
]
