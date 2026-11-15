/**
 * The hero's night atmosphere (sky, faint aurora, a fading grid) and the fictional relief
 * operations ridge that the dashboard window rises in front of. Both are decorative and
 * static, and hidden from assistive technology.
 */

// Deterministic star field (seeded LCG) so every render and screenshot match.
const STARS = (() => {
  let seed = 2182026;
  const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  return Array.from({ length: 150 }, () => ({
    x: rand() * 1440,
    y: rand() * 430,
    r: rand() < 0.1 ? 1.1 : 0.6,
    o: 0.18 + rand() * 0.5,
  }));
})();

export function LandingBackdrop() {
  return (
    <div className="backdrop" aria-hidden="true">
      <div className="backdrop__aurora backdrop__aurora--one" />
      <div className="backdrop__aurora backdrop__aurora--two" />
      <svg className="backdrop__stars" viewBox="0 0 1440 430" preserveAspectRatio="xMidYMin slice">
        {STARS.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#dceaff" opacity={s.o} />
        ))}
      </svg>
      <div className="backdrop__grid" />
    </div>
  );
}

function Tents({ xs, y }: { xs: number[]; y: number }) {
  return (
    <>
      {xs.map((x, i) => (
        <path
          key={x}
          d={`M${x} ${y - (i % 2)}l10-14 10 14Z`}
          fill="#15294a"
          stroke="rgba(170,205,245,0.32)"
          strokeWidth="1"
        />
      ))}
    </>
  );
}

function Marker({ x, y }: { x: number; y: number }) {
  return (
    <>
      <circle cx={x} cy={y} r="3.5" fill="var(--teal)" />
      <circle cx={x} cy={y} r="9" fill="none" stroke="rgba(63,208,201,0.3)" />
    </>
  );
}

/**
 * A night ridge with a depot (warehouse and water tower), three shelter camps and the
 * dashed supply routes between them. Sits directly behind the top edge of the dashboard
 * window, so the window reads as rising out of the landscape.
 *
 * Drawn at a fixed 1:1 scale (1440 x 360 user units = px) so its height never grows with
 * the viewport and cannot climb into the hero copy. The hills extend past the viewBox
 * (x -800 to 2240, drawn with overflow visible) so wide screens still see one continuous
 * horizon; the hero frame clips whatever lies beyond it.
 */
export function LandscapeRidge() {
  return (
    <svg
      className="ridge"
      width="1440"
      height="360"
      viewBox="0 0 1440 360"
      overflow="visible"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M-800 190C-600 170 -160 242 0 206C160 170 300 198 420 180S700 150 860 172S1150 150 1280 176S1400 166 1440 170S1800 150 2240 180V360H-800Z"
        fill="#0b1b2f"
      />
      <path
        d="M-800 238C-600 252 -140 264 0 250C140 236 260 228 380 238S620 262 760 250S1040 228 1180 238S1380 254 1440 246S1800 230 2240 244V360H-800Z"
        fill="#081424"
      />

      {/* Depot: warehouse with loading door and lit windows, plus a water tower */}
      <path d="M216 213 256 199 296 213Z" fill="#17304f" />
      <rect x="220" y="213" width="72" height="24" fill="#142a46" />
      <rect x="249" y="223" width="14" height="14" fill="#1b3655" />
      <rect x="228" y="219" width="5" height="4" fill="#f3cf8a" opacity="0.8" />
      <rect x="237" y="219" width="5" height="4" fill="#f3cf8a" opacity="0.55" />
      <rect x="274" y="219" width="5" height="4" fill="#f3cf8a" opacity="0.75" />
      <g stroke="#183150" strokeWidth="2">
        <path d="M319 236 322 208M336 236 333 208M320 224h15" />
      </g>
      <rect x="313" y="194" width="30" height="15" rx="3" fill="#163050" />

      {/* Camps */}
      <Tents xs={[500, 522, 544]} y={255} />
      <Tents xs={[1094, 1116, 1138, 1166, 1188]} y={240} />
      <g fill="#15294a">
        <path d="M1240 240h18v-10l-9-7-9 7Z" />
        <path d="M1264 242h14v-8l-7-6-7 6Z" />
      </g>

      {/* Supply routes */}
      <g
        fill="none"
        stroke="rgba(127,227,220,0.55)"
        strokeWidth="1.4"
        strokeDasharray="2 7"
        strokeLinecap="round"
      >
        <path d="M300 240C380 254 440 260 494 258" />
        <path d="M570 258C760 264 960 252 1088 242" />
        <path d="M1212 242C1220 242 1228 241 1236 241" />
      </g>

      {/* Markers and labels */}
      <g className="ridge__markers">
        <rect x="252" y="182" width="8" height="8" rx="2" fill="#e8eef7" />
        <Marker x={532} y={222} />
        <Marker x={1141} y={208} />
        <Marker x={1259} y={206} />
      </g>
      <g className="ridge__labels" fontSize="12" letterSpacing="0.08em" textAnchor="middle">
        <text x="256" y="175">
          DEPOT
        </text>
        <text x="532" y="207">
          ZONE C
        </text>
        <text x="1141" y="193">
          ZONE A
        </text>
        <text x="1259" y="191">
          ZONE B
        </text>
      </g>

      <path
        d="M-800 296C-500 304 -240 312 0 300C240 288 480 296 720 292S1200 284 1440 296S1840 300 2240 296V360H-800Z"
        fill="#050b14"
      />
    </svg>
  );
}
