"use client";

import { Navbar } from '@/sections/Navbar';
import { Hero } from '@/sections/Hero';
import { CharactersSection } from '@/sections/CharactersSection';
import { FeaturesSection } from '@/sections/FeaturesSection';
import { HowItWorks } from '@/sections/HowItWorks';
import { Testimonials } from '@/sections/Testimonials';
import { PricingSection } from '@/sections/PricingSection';
import { CTASection } from '@/sections/CTASection';
import { Footer } from '@/sections/Footer';

export default function MarketingHomepage() {
  return (
    <div className="min-h-screen bg-cyber-black text-white overflow-x-hidden bg-black selection:bg-cyber-pink/30">
      <Navbar />
      <main>
        <Hero />
        <CharactersSection />
        <FeaturesSection />
        <HowItWorks />
        <Testimonials />
        <PricingSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
