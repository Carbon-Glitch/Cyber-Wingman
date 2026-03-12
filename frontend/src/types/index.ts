export interface Character {
  id: string;
  name: string;
  title: string;
  tag: string;
  color: 'pink' | 'cyan' | 'amber' | 'purple';
  traits: string[];
  description: string;
  image: string;
}

export interface Feature {
  id: string;
  title: string;
  description: string;
  highlights: string[];
}

export interface PricingPlan {
  id: string;
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  popular?: boolean;
  cta: string;
}

export interface Testimonial {
  id: string;
  quote: string;
  author: string;
  character: string;
}
