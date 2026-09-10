import React from 'react';
import { Composition, Sequence, interpolate, Easing, useCurrentFrame, AbsoluteFill } from 'remotion';
import { FPS, TOTAL_FRAMES, SCENES, BG } from './constants';
import { Scene1Title } from './Scene1Title';
import { Scene2Idea } from './Scene2Idea';
import { Scene3Pipeline } from './Scene3Pipeline';
import { Scene4Score } from './Scene4Score';
import { Scene5Ready } from './Scene5Ready';
import { Scene6CTA } from './Scene6CTA';

// Wraps a scene in a Sequence with opacity-based fade-in/out.
// `from` and `durationInFrames` are in the global timeline.
// The component inside receives a LOCAL useCurrentFrame() from Sequence.
const FadedScene: React.FC<{
  from: number;
  durationInFrames: number;
  fadeIn?: number;
  fadeOut?: number;
  children: React.ReactNode;
}> = ({ from, durationInFrames, fadeIn = 8, fadeOut = 8, children }) => {
  return (
    <Sequence from={from} durationInFrames={durationInFrames} layout="none">
      <FadeOverlay fadeIn={fadeIn} fadeOut={fadeOut} durationInFrames={durationInFrames}>
        {children}
      </FadeOverlay>
    </Sequence>
  );
};

const FadeOverlay: React.FC<{
  fadeIn: number;
  fadeOut: number;
  durationInFrames: number;
  children: React.ReactNode;
}> = ({ fadeIn, fadeOut, durationInFrames, children }) => {
  const frame = useCurrentFrame();

  // Guard: if fadeIn <= 0, skip the in-interpolation entirely
  const opacityIn =
    fadeIn > 0
      ? interpolate(frame, [0, Math.max(fadeIn, 1)], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.out(Easing.cubic),
        })
      : 1;

  // Guard: if fadeOut <= 0, skip the out-interpolation entirely
  const opacityOut =
    fadeOut > 0
      ? interpolate(
          frame,
          [Math.max(durationInFrames - fadeOut, 0), Math.max(durationInFrames, 1)],
          [1, 0],
          {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.in(Easing.cubic),
          }
        )
      : 1;

  return (
    <AbsoluteFill style={{ opacity: Math.min(opacityIn, opacityOut) }}>
      {children}
    </AbsoluteFill>
  );
};

const FADE = 8; // frames

const MainComposition: React.FC = () => {
  // Scene durations with FADE overlap on each side
  const s1Dur = SCENES.s1.end - SCENES.s1.start + FADE;
  const s2Dur = SCENES.s2.end - SCENES.s2.start + FADE * 2;
  const s3Dur = SCENES.s3.end - SCENES.s3.start + FADE * 2;
  const s4Dur = SCENES.s4.end - SCENES.s4.start + FADE * 2;
  const s5Dur = SCENES.s5.end - SCENES.s5.start + FADE * 2;
  const s6Dur = SCENES.s6.end - SCENES.s6.start + FADE;

  return (
    <AbsoluteFill style={{ background: BG }}>
      <FadedScene from={SCENES.s1.start} durationInFrames={s1Dur} fadeIn={FADE} fadeOut={FADE}>
        <Scene1Title />
      </FadedScene>

      <FadedScene from={SCENES.s2.start - FADE} durationInFrames={s2Dur} fadeIn={FADE} fadeOut={FADE}>
        <Scene2Idea />
      </FadedScene>

      <FadedScene from={SCENES.s3.start - FADE} durationInFrames={s3Dur} fadeIn={FADE} fadeOut={FADE}>
        <Scene3Pipeline />
      </FadedScene>

      <FadedScene from={SCENES.s4.start - FADE} durationInFrames={s4Dur} fadeIn={FADE} fadeOut={FADE}>
        <Scene4Score />
      </FadedScene>

      <FadedScene from={SCENES.s5.start - FADE} durationInFrames={s5Dur} fadeIn={FADE} fadeOut={FADE}>
        <Scene5Ready />
      </FadedScene>

      <FadedScene from={SCENES.s6.start - FADE} durationInFrames={s6Dur} fadeIn={FADE} fadeOut={0}>
        <Scene6CTA />
      </FadedScene>
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BookGenesis50Demo"
        component={MainComposition}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
