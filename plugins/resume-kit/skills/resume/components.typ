// components.typ — reusable layout pieces for the resume.io-style two-column
// design. Every constant in `geo` is a measured value, and design-spec.md
// §1-§6 records where each one came from and why it is not the number a
// ruler would give. Read that before changing one, and run
// tools/check-fidelity.sh after: it is what catches a change that moved the
// rendered page.

#let geo = (
  page-width: 595.28pt,
  page-height: 841.89pt,
  // Not the "true" 44pt: a fresh Typst page's first line of *body* text
  // (the case that matters on page 2/3, which open mid-bullet) sits 2.06pt
  // above the nominal margin-top box edge. sidebar-top is an absolute
  // value from the true page edge (independent of this), so it needs no
  // matching adjustment. Page 1's extra offset (the 22pt Oswald name sits
  // further above its own box top than body text does) is handled
  // separately by `pad-top`, below — same split the retired HTML pipeline's own
  // design-spec.md §6 point 3 makes for the analogous Chrome quirk.
  margin-top: 46.06pt,
  // Extra space added once, before the name only, on top of margin-top —
  // page 1 opens with the name (not body text), whose own box-top-to-ink
  // offset is 5.89pt bigger than body text's (7.95pt vs 2.06pt).
  pad-top: 5.89pt,
  margin-bottom: 44pt,
  margin-left: 42pt,
  // Not the "true" 329.28pt react-pdf measurement: Typst's Lato shaping,
  // like Chrome's, wraps one word early at that width. All matched lines
  // reproduce their target break anywhere in [336.15, 336.5]pt — a plateau
  // almost identical to the HTML version's own [335, 338]pt one — found by
  // sweeping col-width and counting how many lines kept the calibration
  // reference's own line breaks.
  col-width: 336.3pt,
  sidebar-x: 403.28pt,
  sidebar-pad-left: 34pt,
  navy: rgb("#082A4D"),
  ink: rgb("#0D111A"),
  date-grey: rgb("#959BA6"),
  name-size: 22pt,
  subtitle-size: 6pt,
  section-title-size: 14pt,
  body-size: 9pt,
  body-leading: 12.825pt,
  // Typst's par.leading is added on top of Lato 9pt's own natural
  // single-line metric (empirically 6.448pt for this font/size, found by
  // measuring the on-page pitch of two leading values and solving the
  // linear relationship), unlike CSS's line-height which IS the total
  // pitch. leading = body-leading - body-line-const reproduces the true
  // 12.825pt baseline-to-baseline pitch.
  body-line-const: 6.448pt,
  job-title-size: 10pt,
  date-size: 6pt,
  bullet-indent: 13pt,       // glyph at x = margin-left + 13pt = 55pt
  // Typst's list body-indent is measured from the marker's own right edge,
  // not from the paragraph left like the HTML version's CSS padding-left —
  // so it must be shortened by the "•" glyph's own rendered width (~5.22pt
  // at 9pt Lato) to land text at the same x = margin-left + 22pt = 64pt.
  bullet-body-indent: 3.78pt,
  // Date-line separator. Was an em dash, matching the resume.io reference;
  // this renderer emits no em or en dashes anywhere, so it is a plain
  // hyphen. See design-spec.md §3.
  date-sep: "-",
  // Main-column vertical gaps. Starting hypotheses are the retired HTML pipeline's tuned CSS custom properties (its template.html :root block) — the best
  // available approximation of the true react-pdf rhythm, since Typst has
  // no equivalent "true" measurement of its own. Recalibrated in Task 6
  // against Typst's own box model, which does not collapse margins or
  // round line-height the way Chrome's does.
  gap-name-subtitle: 12.93pt,
  gap-subtitle-section: 23.93pt,
  gap-section-summary: 11.54pt,
  gap-summary-section: 20.93pt,
  gap-section-job: 12.26pt,
  gap-bullets-job: 15.73pt,
  gap-title-date: 8.44pt,
  gap-date-bullets: 7.81pt,
  // Each bullet is wrapped in its own single-item `list()` (so a bullet
  // never splits across a page break, per the pagination rules) instead of
  // one shared list — Typst's `list.spacing` (which governs the gap
  // between items of a single list) doesn't apply between separate list
  // instances, so the gap between two bullets must be inserted explicitly.
  gap-bullet-bullet: 6.40pt,
  // Recalibrated against the calibration reference once content.yaml
  // regained a populated Education entry — previously unexercised
  // (education: []), so these three were pure guesses. Solved directly from measured
  // y-positions rather than by trial-and-error: each transition's
  // intrinsic (font-metric) advance is constant regardless of the `v()`
  // gap value, so `new = old + (true_gap - measured_gap)` is exact in one
  // step, not an iterative search.
  gap-bullets-section: 22.00pt,
  gap-section-edu: 11.77pt,
  gap-edu-year: 8.56pt,
  // Gap between a later education entry and the one before it. Still
  // copied from gap-bullets-job as a placeholder, not independently
  // measured — the transition between two education entries in a
  // content file that has more than one has no measured calibration
  // data behind it. See design-spec.md §4/§6.
  gap-edu-edu: 15.73pt,
  // Details heading ink-top, from design-spec.md §4. Confirmed correct
  // as-is against the real reference (generated 107.77pt vs true
  // 107.65-107.70pt, well within tolerance) — the earlier "8.32pt too big"
  // note below was itself a symptom of calibrating against the wrong
  // reference (see that note's replacement), not a problem with this value.
  sidebar-top: 111.22pt,
  sidebar-title-size: 9pt,
  sidebar-item-size: 8pt,
  // (block, heading->item, item->item, item->next-heading). Recalibrated
  // against the calibration reference with real multi-item Skills (8
  // items) and Hobbies (5 items) content — the previous values here were
  // tuned against an HTML/Chrome build of the same content, used as a
  // stand-in reference before a real resume.io export was available) with
  // only single-item blocks, and that proxy's own Chrome-specific line
  // metrics don't match Typst's, which is why they were off once real
  // multi-item content exercised them. Solved the same direct way as the
  // education gaps above (measure the constant intrinsic advance per
  // transition type, then `new = old + (true_gap - measured_gap)`).
  sb-rhythm: (
    details: (9.76pt, 7.57pt, 23.30pt),
    links: (9.76pt, 9.92pt, 21.40pt),
    skills: (9.76pt, 9.92pt, 21.40pt),
    hobbies: (9.76pt, 5.67pt, 0pt),
  ),
)

// Full-bleed navy band, for use as `page(background: sidebar-band())`.
// Independent of page margins — confirmed by spike to reach the true page
// edge regardless of the `right` margin value.
#let sidebar-band() = place(top + left, dx: geo.sidebar-x, dy: 0pt, rect(
  width: geo.page-width - geo.sidebar-x,
  height: geo.page-height,
  fill: geo.navy,
))

#let section-heading(title) = text(
  font: "Oswald", weight: 500, size: geo.section-title-size,
)[#title]

// A mid-word "-" (e.g. "e-commerce", "latency-breach") is a valid line-break
// point to Typst, same as a space. When a line breaks there, the hyphen
// stays as the last glyph on one line and the word continues on the next -
// correct on the page, but pdftotext's dehyphenation heuristic then treats
// that hyphen as line-wrap scaffolding and drops it, fusing the two halves
// ("latencybreach", "ecommerce"). A non-breaking hyphen (U+2011) renders
// identically but is never a break point, so the word moves to the next
// line as a whole and the ambiguity pdftotext is guessing at never arises.
// Only a hyphen with a non-space character on both sides is touched, so a
// bullet's own leading "-" (none exist; markers are the list glyph) or a
// numeric range would pass through untouched.
// A single pass misses chained single-character segments ("A-B-C"): the
// first match consumes "H-E", leaving no unconsumed character before the
// second hyphen for a non-overlapping regex pass to match against. Three
// passes converges on any chain length this content actually has (longest
// observed is two hyphens); each pass only touches hyphens still literal,
// since a converted one is U+2011, not "-", and won't match again.
#let nbh(s) = if type(s) == str {
  let fixed = s
  for _ in range(3) {
    fixed = fixed.replace(regex("(\S)-(\S)"), m => m.captures.at(0) + "\u{2011}" + m.captures.at(1))
  }
  fixed
} else { s }

#let bullet-item(item) = {
  set list(marker: [•], indent: geo.bullet-indent, body-indent: geo.bullet-body-indent)
  set text(size: geo.body-size)
  set par(leading: geo.body-leading - geo.body-line-const, spacing: 0pt)
  block(breakable: false, list(nbh(item)))
}

#let bullet-list(items) = {
  for (i, item) in items.enumerate() {
    if i > 0 { v(geo.gap-bullet-bullet) }
    bullet-item(item)
  }
}

// Deviation from the plan's dot-access version: this skill has no Python
// build layer to normalise the content dict (the retired HTML pipeline had
// one). So `location`/`end`/`bullets` on a job and `year` on an education
// entry are read with `.at(..., default: ...)` to stay safe if a future
// content.yaml omits one of them.
#let job-entry(job) = {
  let location = job.at("location", default: "")
  let end = job.at("end", default: none)
  let bullets = job.at("bullets", default: ())
  let heading = [
    #text(weight: 700, size: geo.job-title-size)[
      #nbh(job.role), #nbh(job.company)#if location != none and location != "" [, #nbh(location)]
    ]
    #v(geo.gap-title-date)
    #text(size: geo.date-size, tracking: 1pt, fill: geo.date-grey)[
      #upper(if end != none { job.start + " " + geo.date-sep + " " + end } else { job.start })
    ]
  ]
  if bullets.len() > 0 {
    block(breakable: false)[
      #heading
      #v(geo.gap-date-bullets)
      #bullet-item(bullets.first())
    ]
    if bullets.len() > 1 {
      v(geo.gap-bullet-bullet)
      bullet-list(bullets.slice(1))
    }
  } else {
    block(breakable: false, heading)
  }
}

#let edu-entry(edu) = {
  // YAML parses a bare `year: 2015` as an integer, not a string — str()
  // normalizes both cases before upper(), which requires a string.
  let year = str(edu.at("year", default: ""))
  block(breakable: false)[
    // Explicit leading so a wrapped degree+school line reproduces the
    // reference's measured 14.25pt wrap pitch (design-spec.md §4)
    // instead of Typst's default ~0.65em paragraph leading.
    #set par(leading: 7.02pt)
    #text(weight: 700, size: geo.job-title-size)[#nbh(edu.degree), #nbh(edu.school)]
    #v(geo.gap-edu-year)
    #text(size: geo.date-size, tracking: 1pt, fill: geo.date-grey)[#if year != none and year != "" [#upper(year)]]
  ]
}

#let sidebar-item(it) = {
  if type(it) == dictionary {
    underline(link(it.link)[#it.text])
  } else {
    nbh(it)
  }
}

// `key` selects the (heading-gap, item-gap, trailing-gap) triple from
// geo.sb-rhythm. Returns none (renders nothing) for an empty `items` list,
// so an omitted section produces no heading — matching the retired HTML pipeline's
// "every section is optional" rule.
#let sidebar-block(key, title, items) = {
  if items.len() == 0 { return }
  let (head-gap, item-gap, _) = geo.sb-rhythm.at(key)
  set text(fill: white)
  text(font: "Oswald", weight: 500, size: geo.sidebar-title-size)[#title]
  v(head-gap)
  for (i, it) in items.enumerate() [
    #if i > 0 { v(item-gap) }
    #text(size: geo.sidebar-item-size)[#sidebar-item(it)]
  ]
}
