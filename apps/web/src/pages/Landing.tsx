import { useGSAP } from '@gsap/react';
import { useRef } from 'react';
import { AboutSection } from '../components/AboutSection';
import { DashboardPreview } from '../components/DashboardPreview';
import { DashboardReveal } from '../components/DashboardReveal';
import { FeatureExplorer } from '../components/FeatureExplorer';
import { HowItWorks } from '../components/HowItWorks';
import { LandingBackdrop, LandscapeRidge } from '../components/LandingBackdrop';
import { LandingHero } from '../components/LandingHero';
import { MethodologyPreview } from '../components/MethodologyPreview';
import { SiteHeader } from '../components/SiteHeader';
import { SiteFooter } from '../components/SiteFooter';
import { ResourceStory } from '../components/story/ResourceStory';
import { EASE_OUT, gsap } from '../lib/motion';
import '../styles/landing.css';
import '../styles/story.css';

/**
 * Scroll motion for the landing page. Every tween is scrubbed by native scroll or plays
 * once; nothing hides content before the script runs, and reduced motion gets none of it.
 */
function useLandingMotion(scope: React.RefObject<HTMLDivElement | null>) {
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(
        {
          motion: '(prefers-reduced-motion: no-preference)',
          wide: '(min-width: 901px)',
        },
        (ctx) => {
          const { motion, wide } = ctx.conditions as { motion: boolean; wide: boolean };
          if (!motion) return;

          // Scene 1: the atmosphere drifts slower than the page, the copy recedes, and the
          // dashboard window comes forward as the visitor starts to scroll.
          const hero = { trigger: '.hero-frame', start: 'top top', end: 'bottom top', scrub: 0.6 };
          gsap.to('.backdrop__stars, .backdrop__aurora', {
            yPercent: 14,
            ease: 'none',
            scrollTrigger: hero,
          });
          gsap.to('.hero', {
            y: -64,
            autoAlpha: 0,
            ease: 'none',
            scrollTrigger: { ...hero, end: '58% top' },
          });
          gsap.to('.hero-frame .ridge', { '--ridge-y': '26px', ease: 'none', scrollTrigger: hero });
          if (wide) {
            gsap.to('.hero-frame .preview', {
              y: -36,
              scale: 1.035,
              ease: 'none',
              scrollTrigger: { ...hero, end: '70% top' },
            });
          }

          // The five workflow steps arrive as the list they are.
          gsap.from('.workflow__step', {
            y: 14,
            autoAlpha: 0,
            duration: 0.6,
            ease: EASE_OUT,
            stagger: 0.07,
            scrollTrigger: { trigger: '.workflow__steps', start: 'top 85%', once: true },
          });

          // Scene 5: the preview squares up to the viewer as it reaches the centre.
          gsap.fromTo(
            '.reveal__stage .preview__window',
            { rotateX: wide ? 16 : 8, scale: 0.94, transformOrigin: '50% 100%' },
            {
              rotateX: 0,
              scale: 1,
              ease: 'none',
              scrollTrigger: {
                trigger: '.reveal',
                start: 'top bottom',
                end: 'center 55%',
                scrub: 0.6,
              },
            },
          );
        },
      );
      return () => mm.revert();
    },
    { scope },
  );
}

/** Public landing page at "/". Frontend-only: it renders without the backend. */
export default function Landing() {
  const root = useRef<HTMLDivElement>(null);
  useLandingMotion(root);

  return (
    <div className="landing" ref={root}>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {/* The header sits over the hero frame but stays outside <main> as the banner landmark. */}
      <SiteHeader />
      <main id="main" tabIndex={-1}>
        <div className="hero-frame">
          <LandingBackdrop />
          <LandingHero />
          <div className="hero-stage">
            <LandscapeRidge />
            <DashboardPreview />
          </div>
        </div>
        <ResourceStory />
        <HowItWorks />
        <FeatureExplorer />
        <MethodologyPreview />
        <AboutSection />
        <DashboardReveal />
      </main>
      <SiteFooter />
    </div>
  );
}
