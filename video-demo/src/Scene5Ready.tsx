import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { BG, WHITE, PURPLE_LIGHT, GREEN, GRAY, GRAY_DIM } from './constants';

const BADGES = [
  { label: 'saved project files', color: PURPLE_LIGHT },
  { label: 'editorial review loop', color: PURPLE_LIGHT },
  { label: 'you remain the author', color: GREEN },
];

export const Scene5Ready: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const mainFade = interpolate(frame, [0, fps * 0.6], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const mainSlide = interpolate(frame, [0, fps * 0.6], [24, 0], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const subFade = interpolate(frame, [fps * 0.5, fps * 1.1], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const badgeFade = (i: number) =>
    interpolate(frame, [fps * (0.7 + i * 0.18), fps * (1.1 + i * 0.18)], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: BG,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        padding: '0 120px',
        boxSizing: 'border-box',
      }}
    >
      {/* Grid bg */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Glow behind text */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 300,
          borderRadius: '50%',
          background: 'radial-gradient(ellipse, rgba(34,197,94,0.08) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      <div style={{ textAlign: 'center', zIndex: 1 }}>
        {/* Main headline */}
        <div
          style={{
            opacity: mainFade,
            transform: `translateY(${mainSlide}px)`,
            fontSize: 80,
            fontWeight: 800,
            color: WHITE,
            letterSpacing: '-2px',
            lineHeight: 1.05,
          }}
        >
          Your next chapter is ready.
        </div>

        {/* Divider */}
        <div
          style={{
            opacity: subFade,
            width: 80,
            height: 2,
            background: GREEN,
            margin: '24px auto',
            borderRadius: 2,
          }}
        />

        {/* Badges row */}
        <div
          style={{
            display: 'flex',
            gap: 16,
            justifyContent: 'center',
            flexWrap: 'wrap',
          }}
        >
          {BADGES.map((badge, i) => (
            <div
              key={i}
              style={{
                opacity: badgeFade(i),
                fontFamily: "'Courier New', monospace",
                fontSize: 15,
                color: badge.color,
                background: `${badge.color}14`,
                border: `1px solid ${badge.color}35`,
                borderRadius: 8,
                padding: '8px 18px',
                letterSpacing: '0.04em',
              }}
            >
              {badge.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
