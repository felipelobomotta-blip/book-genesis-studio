import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BG, GRAY, GRAY_DIM, GREEN, PURPLE, PURPLE_LIGHT, WHITE, AMBER } from './constants';

const INSTALL_LINES = [
  '$ git clone https://github.com/felipelobomotta-blip/book-genesis-studio.git',
  '$ cd book-genesis-studio',
  '$ python runner/installer.py install claude --dest .book-genesis-demo --force',
  'install: beta-reader',
  'install: book-genesis',
  'install: book-researcher',
  'install: prose-craft',
  'install: series-architect',
  'Installed for claude: .book-genesis-demo',
];

const VERIFY_LINES = [
  '$ python runner/installer.py verify-install claude --dest .book-genesis-demo',
  'Checking installed skills: .book-genesis-demo',
  'Installed files verified.',
  'Confirm discovery in the native host; no model was tested.',
];

const HOST_LINES = [
  '> Use the book-genesis skill.',
  '> Write in English.',
  '> My idea is a mystery about a retired train dispatcher',
  '> who finds a farewell letter inside a station clock.',
  '',
  'Book Genesis → intake started',
  'Saved → PROJECT_STATE.yaml',
  'Saved → artifacts/brief.md',
  'Next → choose the direction with the author',
];

const RESUME_LINES = [
  '> Read PROJECT_STATE.yaml and continue from the next phase.',
  '',
  '✓ state loaded from the project folder',
  '✓ existing artifacts preserved',
  '→ next phase: Foundation',
  'The host owns the model, tools, quota, and permissions.',
];

const fade = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, start + 12, end - 12, end], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });

const WindowChrome: React.FC<{ title: string; status?: string }> = ({ title, status }) => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      {['#ff5f57', '#febc2e', '#28c840'].map((color) => (
        <span key={color} style={{ width: 11, height: 11, borderRadius: '50%', background: color }} />
      ))}
      <span style={{ marginLeft: 10, color: GRAY, fontSize: 14, fontFamily: "'Courier New', monospace" }}>{title}</span>
    </div>
    {status && <span style={{ color: GREEN, fontSize: 13, fontFamily: "'Courier New', monospace" }}>● {status}</span>}
  </div>
);

const Terminal: React.FC<{ lines: string[]; frame: number; speed?: number; accent?: string }> = ({
  lines,
  frame,
  speed = 7,
  accent = PURPLE_LIGHT,
}) => {
  const visible = Math.min(lines.length, Math.max(0, Math.floor(frame / speed) + 1));
  return (
    <div style={{ fontFamily: "'Cascadia Code', 'Courier New', monospace", fontSize: 20, lineHeight: 1.62 }}>
      {lines.slice(0, visible).map((line, index) => {
        const isCommand = line.startsWith('$') || line.startsWith('>');
        const isSuccess = line.startsWith('✓') || line.startsWith('Installed files verified');
        const color = isSuccess ? GREEN : isCommand ? WHITE : index === visible - 1 ? accent : GRAY;
        return (
          <div key={`${line}-${index}`} style={{ color, whiteSpace: 'pre-wrap', minHeight: 32 }}>
            {line || ' '}
            {index === visible - 1 && visible < lines.length && (
              <span style={{ display: 'inline-block', width: 10, height: 22, background: accent, marginLeft: 4, verticalAlign: '-2px' }} />
            )}
          </div>
        );
      })}
    </div>
  );
};

const Shell: React.FC<{ children: React.ReactNode; label: string; note?: string }> = ({ children, label, note }) => (
  <AbsoluteFill style={{ background: BG, color: WHITE, fontFamily: "'Segoe UI', system-ui, sans-serif", padding: '70px 120px' }}>
    <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(124,58,237,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.035) 1px, transparent 1px)', backgroundSize: '64px 64px' }} />
    <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 44 }}>
      <span style={{ fontWeight: 750, fontSize: 22, letterSpacing: '-0.02em' }}>Book Genesis <span style={{ color: PURPLE_LIGHT }}>5.0</span></span>
      <span style={{ color: GRAY_DIM, fontFamily: "'Courier New', monospace", fontSize: 13, letterSpacing: '0.14em' }}>{label.toUpperCase()}</span>
    </div>
    <div style={{ position: 'relative', zIndex: 1, flex: 1 }}>{children}</div>
    {note && <div style={{ position: 'absolute', zIndex: 2, left: 120, bottom: 42, color: GRAY_DIM, fontFamily: "'Courier New', monospace", fontSize: 13 }}>{note}</div>}
  </AbsoluteFill>
);

const InstallScene: React.FC<{ frame: number }> = ({ frame }) => (
  <Shell label="1 · install" note="Observed local command · maintainer installer only">
    <div style={{ maxWidth: 1320, margin: '0 auto' }}>
      <h2 style={{ fontSize: 54, margin: '0 0 12px', letterSpacing: '-0.04em' }}>Install the writing skills.</h2>
      <p style={{ color: GRAY, fontSize: 21, margin: '0 0 32px' }}>One command copies the same portable bundle into your chosen host.</p>
      <div style={{ background: 'rgba(9,13,28,0.92)', border: '1px solid rgba(168,85,247,0.38)', borderRadius: 18, padding: '30px 34px', boxShadow: '0 24px 80px rgba(0,0,0,0.28)' }}>
        <WindowChrome title="PowerShell · book-genesis-studio" status="local" />
        <Terminal lines={INSTALL_LINES} frame={frame} />
      </div>
    </div>
  </Shell>
);

const VerifyScene: React.FC<{ frame: number }> = ({ frame }) => (
  <Shell label="2 · verify" note="The installer never calls a model">
    <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: 44, alignItems: 'center', maxWidth: 1420, margin: '0 auto' }}>
      <div>
        <div style={{ color: GREEN, fontFamily: "'Courier New', monospace", fontSize: 14, letterSpacing: '0.14em', marginBottom: 18 }}>CHECKSUM-BACKED FILE INTEGRITY</div>
        <h2 style={{ fontSize: 56, margin: '0 0 18px', letterSpacing: '-0.04em' }}>Know what was installed.</h2>
        <p style={{ color: GRAY, fontSize: 21, lineHeight: 1.45, maxWidth: 620 }}>The verifier checks the skills and references against the checkout. Then your native host discovers them.</p>
        <div style={{ display: 'flex', gap: 12, marginTop: 26, flexWrap: 'wrap' }}>
          {['15 skills', 'Claude Code', 'OpenCode', 'MIT licensed'].map((item) => <span key={item} style={{ color: PURPLE_LIGHT, border: '1px solid rgba(168,85,247,0.35)', background: 'rgba(124,58,237,0.09)', borderRadius: 999, padding: '9px 15px', fontFamily: "'Courier New', monospace", fontSize: 14 }}>{item}</span>)}
        </div>
      </div>
      <div style={{ background: 'rgba(9,13,28,0.92)', border: '1px solid rgba(34,197,94,0.38)', borderRadius: 18, padding: '30px 34px' }}>
        <WindowChrome title="PowerShell · verification" status="verified" />
        <Terminal lines={VERIFY_LINES} frame={frame} speed={12} accent={GREEN} />
      </div>
    </div>
  </Shell>
);

const HostScene: React.FC<{ frame: number }> = ({ frame }) => (
  <Shell label="3 · use your host" note="Example host transcript · run with your own account">
    <div style={{ maxWidth: 1420, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginBottom: 22 }}>
        <div><div style={{ color: PURPLE_LIGHT, fontFamily: "'Courier New', monospace", fontSize: 14, letterSpacing: '0.14em', marginBottom: 14 }}>CLAUDE CODE / OPENCODE / CODEX</div><h2 style={{ fontSize: 52, margin: 0, letterSpacing: '-0.04em' }}>Give the idea to the agent.</h2></div>
        <div style={{ color: GRAY_DIM, fontFamily: "'Courier New', monospace", fontSize: 14 }}>host session</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 0.78fr', gap: 24 }}>
        <div style={{ background: 'rgba(9,13,28,0.92)', border: '1px solid rgba(168,85,247,0.35)', borderRadius: 18, padding: '28px 32px' }}><WindowChrome title="Claude Code · book project" status="ready" /><Terminal lines={HOST_LINES} frame={frame} speed={8} /></div>
        <div style={{ background: 'rgba(255,255,255,0.035)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 18, padding: '28px 30px' }}>
          <div style={{ color: GRAY_DIM, fontFamily: "'Courier New', monospace", fontSize: 13, marginBottom: 22 }}>BOOK PROJECT / FILES</div>
          {['PROJECT_STATE.yaml', 'artifacts/brief.md', 'artifacts/story-engine.md', 'manuscript/chapters/'].map((file, index) => <div key={file} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '13px 0', borderBottom: index === 3 ? 'none' : '1px solid rgba(255,255,255,0.07)', color: index === 0 ? GREEN : WHITE, fontFamily: "'Courier New', monospace", fontSize: 15 }}><span style={{ color: index === 0 ? GREEN : PURPLE_LIGHT }}>{index === 3 ? '▱' : '▤'}</span>{file}</div>)}
          <div style={{ marginTop: 28, padding: '14px 16px', background: 'rgba(34,197,94,0.09)', border: '1px solid rgba(34,197,94,0.25)', borderRadius: 10, color: GREEN, fontFamily: "'Courier New', monospace", fontSize: 13 }}>saved to your project folder</div>
        </div>
      </div>
    </div>
  </Shell>
);

const ResumeScene: React.FC<{ frame: number }> = ({ frame }) => (
  <Shell label="4 · resume" note="Files make the workflow portable across sessions and hosts">
    <div style={{ maxWidth: 1180, margin: '0 auto', textAlign: 'center' }}>
      <div style={{ color: AMBER, fontFamily: "'Courier New', monospace", fontSize: 14, letterSpacing: '0.14em', marginBottom: 18 }}>NEW SESSION · SAME PROJECT</div>
      <h2 style={{ fontSize: 58, margin: '0 0 16px', letterSpacing: '-0.04em' }}>Stop. Return. Continue.</h2>
      <p style={{ color: GRAY, fontSize: 21, margin: '0 auto 30px', maxWidth: 720 }}>Your agent reads the saved state and tells you what comes next. You stay in control of every creative decision.</p>
      <div style={{ textAlign: 'left', background: 'rgba(9,13,28,0.92)', border: '1px solid rgba(245,158,11,0.35)', borderRadius: 18, padding: '30px 36px' }}><WindowChrome title="New host session" status="resumed" /><Terminal lines={RESUME_LINES} frame={frame} speed={10} accent={AMBER} /></div>
    </div>
  </Shell>
);

const CTA: React.FC<{ frame: number }> = ({ frame }) => {
  const pulse = 0.85 + Math.sin(frame / 14) * 0.08;
  return <Shell label="5 · open source">
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
      <div style={{ color: PURPLE_LIGHT, fontFamily: "'Courier New', monospace", fontSize: 14, letterSpacing: '0.18em', marginBottom: 24 }}>YOUR CREATIVITY. YOUR AGENT. YOUR BOOK.</div>
      <h2 style={{ fontSize: 78, margin: '0 0 22px', letterSpacing: '-0.055em' }}>Start with the idea.</h2>
      <div style={{ transform: `scale(${pulse})`, border: '1px solid rgba(168,85,247,0.45)', background: 'rgba(124,58,237,0.12)', borderRadius: 14, padding: '19px 30px', color: WHITE, fontFamily: "'Courier New', monospace", fontSize: 22 }}>github.com/felipelobomotta-blip/book-genesis-studio</div>
      <div style={{ marginTop: 24, color: GRAY, fontSize: 17 }}>MIT licensed · 15 writing skills · 15 installation targets</div>
    </div>
  </Shell>;
};

export const InstallDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sections = [
    { start: 0, end: 4 * fps, render: () => <Title frame={frame} /> },
    { start: 4 * fps, end: 14 * fps, render: () => <InstallScene frame={frame - 4 * fps} /> },
    { start: 14 * fps, end: 22 * fps, render: () => <VerifyScene frame={frame - 14 * fps} /> },
    { start: 22 * fps, end: 34 * fps, render: () => <HostScene frame={frame - 22 * fps} /> },
    { start: 34 * fps, end: 43 * fps, render: () => <ResumeScene frame={frame - 34 * fps} /> },
    { start: 43 * fps, end: 48 * fps, render: () => <CTA frame={frame - 43 * fps} /> },
  ];
  const active = sections.find((section) => frame >= section.start && frame < section.end) || sections[sections.length - 1];
  const opacity = fade(frame, active.start, active.end);
  return <AbsoluteFill style={{ opacity }}>{active.render()}</AbsoluteFill>;
};

const Title: React.FC<{ frame: number }> = ({ frame }) => {
  const rise = interpolate(frame, [0, 45], [30, 0], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const opacity = interpolate(frame, [0, 35], [0, 1], { extrapolateRight: 'clamp' });
  return <Shell label="a real workflow">
    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 80 }}>
      <div style={{ opacity, transform: `translateY(${rise}px)`, maxWidth: 820 }}><div style={{ color: PURPLE_LIGHT, fontFamily: "'Courier New', monospace", fontSize: 15, letterSpacing: '0.16em', marginBottom: 22 }}>A 48-SECOND WALKTHROUGH</div><h1 style={{ fontSize: 78, lineHeight: 1.02, letterSpacing: '-0.06em', margin: 0 }}>Install once.<br /><span style={{ color: GREEN }}>Write with your agent.</span></h1><p style={{ color: GRAY, fontSize: 23, lineHeight: 1.45, maxWidth: 660, marginTop: 28 }}>See the real installer, the file check, the host prompt, and a fresh-session resume.</p></div>
      <div style={{ width: 430, height: 430, borderRadius: '50%', background: 'radial-gradient(circle at 35% 35%, #ffffff 0%, #a855f7 5%, #7c3aed 23%, rgba(124,58,237,0.12) 55%, transparent 72%)', filter: 'drop-shadow(0 0 80px rgba(168,85,247,0.38))' }} />
    </div>
  </Shell>;
};
