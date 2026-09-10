import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { BG, WHITE, PURPLE, PURPLE_LIGHT, GREEN, GRAY, GRAY_DIM } from './constants';

interface Step {
  phase: string;
  label: string;
  tag?: string;
  color: string;
}

const STEPS: Step[] = [
  { phase: '01', label: 'Direction & Research', color: GRAY },
  { phase: '02', label: 'Foundation & Outline', color: PURPLE_LIGHT },
  { phase: '03', label: 'Chapter Drafting', tag: 'save as you go', color: PURPLE_LIGHT },
  { phase: '04', label: 'Adversarial Review', tag: 'find what fails', color: GRAY },
  { phase: '05', label: 'Revision Loop', tag: 'improve the weak spots', color: GREEN },
  { phase: '06', label: 'Editorial Package', color: GREEN },
];

// Each step slides in staggered
const STAGGER_START = 0.3; // seconds delay before first step
const STAGGER_GAP = 0.28;  // seconds between each step

export const Scene3Pipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const timeS = frame / fps;

  // Title fade
  const titleFade = interpolate(frame, [0, fps * 0.5], [0, 1], {
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
        padding: '0 140px',
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

      <div style={{ width: '100%', maxWidth: 900, zIndex: 1 }}>
        {/* Section label */}
        <div
          style={{
            opacity: titleFade,
            fontSize: 13,
            fontFamily: "'Courier New', monospace",
            color: PURPLE_LIGHT,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            marginBottom: 28,
          }}
        >
          // pipeline
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {STEPS.map((step, i) => {
            const stepStart = STAGGER_START + i * STAGGER_GAP;
            const stepFade = interpolate(
              timeS,
              [stepStart, stepStart + 0.35],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
            );
            const stepX = interpolate(
              timeS,
              [stepStart, stepStart + 0.35],
              [-40, 0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
            );

            const isGate = step.tag !== undefined;

            return (
              <div
                key={i}
                style={{
                  opacity: stepFade,
                  transform: `translateX(${stepX}px)`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  background: isGate
                    ? 'rgba(124,58,237,0.08)'
                    : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${isGate ? 'rgba(124,58,237,0.3)' : 'rgba(255,255,255,0.07)'}`,
                  borderRadius: 10,
                  padding: '14px 20px',
                }}
              >
                {/* Left accent bar */}
                <div
                  style={{
                    width: 3,
                    height: 36,
                    borderRadius: 2,
                    background: step.color,
                    flexShrink: 0,
                  }}
                />

                {/* Phase badge */}
                <div
                  style={{
                    fontFamily: "'Courier New', monospace",
                    fontSize: 11,
                    color: GRAY_DIM,
                    letterSpacing: '0.1em',
                    width: 80,
                    flexShrink: 0,
                  }}
                >
                  {step.phase}
                </div>

                {/* Label */}
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 600,
                    color: WHITE,
                    flex: 1,
                  }}
                >
                  {step.label}
                </div>

                {/* Tag */}
                {step.tag && (
                  <div
                    style={{
                      fontFamily: "'Courier New', monospace",
                      fontSize: 12,
                      color: step.color,
                      background: `${step.color}18`,
                      border: `1px solid ${step.color}40`,
                      borderRadius: 6,
                      padding: '4px 10px',
                      letterSpacing: '0.05em',
                    }}
                  >
                    {step.tag}
                  </div>
                )}

                {/* Connector arrow */}
                {i < STEPS.length - 1 && stepFade > 0.5 && (
                  <div style={{ color: GRAY_DIM, fontSize: 16, marginLeft: 4 }}></div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
