import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { BG, WHITE, PURPLE_LIGHT, GRAY } from './constants';

export const Scene1Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, fps * 1.2], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const slideUp = interpolate(frame, [0, fps * 1.2], [32, 0], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const subtitleFade = interpolate(frame, [fps * 0.8, fps * 1.8], [0, 1], {
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
      }}
    >
      {/* Subtle grid background */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Main title */}
      <div
        style={{
          opacity: fadeIn,
          transform: `translateY(${slideUp}px)`,
          textAlign: 'center',
          zIndex: 1,
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 800,
            color: WHITE,
            letterSpacing: '-2px',
            lineHeight: 1.05,
            marginBottom: 8,
          }}
        >
          Book Genesis 5.0
        </div>
        <div
          style={{
            width: 120,
            height: 3,
            background: `linear-gradient(90deg, ${PURPLE_LIGHT}, transparent)`,
            margin: '16px auto',
            borderRadius: 2,
          }}
        />
      </div>

      {/* Subtitle */}
      <div
        style={{
          opacity: subtitleFade,
          zIndex: 1,
          fontFamily: "'Courier New', 'Consolas', monospace",
          fontSize: 22,
          color: GRAY,
          letterSpacing: '0.05em',
          marginTop: 8,
        }}
      >
        your idea → a saved chapter
      </div>
    </div>
  );
};
