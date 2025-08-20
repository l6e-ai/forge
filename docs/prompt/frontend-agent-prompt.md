
# l6e.ai Marketing Site Specification

## 🎯 Site Overview

**Domain**: `l6e.ai`  
**Brand**: Localize AI (l6e)  
**Target**: Developers building local AI applications  
**Goal**: Drive downloads of l6e/forge and build developer community  

## 📱 Site Structure

### **Single Page Application (SPA)**
Modern, fast-loading single page with smooth scrolling sections:

1. **Hero Section** - Value proposition & CTA
2. **Problem/Solution** - Why local AI matters
3. **Product Demo** - l6e/forge in action
4. **Features** - Key capabilities
5. **Getting Started** - Installation & quickstart
6. **Community** - GitHub, docs, support
7. **Footer** - Links, social, legal

## 🎨 Design Requirements

### **Visual Style**
- **Modern, clean, developer-focused**
- **Dark mode primary** with light mode toggle
- **Monospace fonts** for code elements
- **Terminal/CLI aesthetic** throughout
- **Subtle animations** for engagement
- **Mobile-first responsive** design

### **Color Palette**
```css
/* Dark Mode (Primary) */
--bg-primary: #0a0a0a
--bg-secondary: #1a1a1a
--text-primary: #ffffff
--text-secondary: #a0a0a0
--accent: #00ff88 (bright green - local/active)
--accent-secondary: #0088ff (blue - tech)

/* Light Mode */
--bg-primary: #ffffff
--bg-secondary: #f8f9fa
--text-primary: #1a1a1a
--text-secondary: #666666
```

### **Typography**
- **Headings**: Inter or similar (clean, modern)
- **Body**: Inter or similar
- **Code**: JetBrains Mono or Fira Code
- **Logo**: Custom or modified Inter

## 📝 Content Strategy

### **Core Messaging**
- **Primary**: "l6e AI - Localizing AI for everyone"
- **Secondary**: "Create portable AI agents that run anywhere"
- **Distribution**: "Build once, run on any machine"

### **Key Value Props**
1. **Portable**: Package agents that run on any compatible machine
2. **Private**: AI that never leaves your infrastructure
3. **Distributed**: Share agents without sharing data
4. **Cost-Effective**: No cloud fees, no API limits
5. **Independent**: Your AI, your hardware, your control
6. **Universal**: Works on laptops, servers, edge devices

## 🚀 Detailed Section Specs

### **1. Hero Section**
```
[LOGO: l6e AI] [NAV: Docs | GitHub | Community]

[Large Heading]
l6e AI
Localizing AI for everyone

[Subheading]
Create portable AI agents that run anywhere.
Build once, deploy everywhere. No cloud required.

[Primary CTA Button] Create Your First Agent
[Secondary CTA] View on GitHub

[Terminal Demo - Auto-typing animation]
$ pip install l6e-forge
$ l6e create assistant --template=personal
$ l6e package assistant
📦 Packaged assistant.l6e (ready to deploy)
$ l6e deploy assistant.l6e --target=production
🚀 Agent deployed locally
✨ Your AI runs where you need it.
```

### **2. Problem/Solution Section**
```
[Split Layout - Problem | Solution]

❌ Cloud AI Problems              ✅ l6e AI Solutions
• Data leaves your control       • AI runs on your infrastructure
• Ongoing API costs             • One-time setup, no usage fees
• Internet dependency          • Works completely offline
• Vendor lock-in               • Open, portable agent format
• Complex deployment           • Package once, run anywhere
• Privacy concerns             • Your data never leaves your network

[Use Cases Grid]
💼 Enterprise                  🏠 Personal Use              🏭 Edge Computing
Deploy AI in your             Run AI assistants            Distribute AI to
secure environment           on personal devices          remote locations

[Statistics/Social Proof]
"Powering local AI for 1000+ organizations"
"⭐ 2.5k stars on GitHub"
"🔥 Featured in AI infrastructure newsletters"
```

### **3. Live Demo Section**
```
[Heading] From Idea to Deployed Agent in Minutes

[Video/GIF Demo showing:]
1. l6e create support-bot --template=customer-service
2. Code editor with agent.py open (customization)
3. l6e test support-bot (local testing)
4. l6e package support-bot (creates .l6e file)
5. Copying .l6e file to another machine
6. l6e deploy support-bot.l6e (runs on new machine)
7. Agent working identically on both machines

[Call-out boxes highlighting:]
• "Create → Test → Package → Deploy"
• "Same agent, any compatible machine"
• "No cloud accounts or API keys required"
• "Your AI travels with your data policies"
```

### **4. Features Grid**
```
[3x2 Grid Layout]

📦 Portable Agents            🏠 Local Infrastructure
Package agents that run       Deploy on your hardware.
anywhere. Build once,         No cloud dependencies.
deploy everywhere.            Complete data sovereignty.

🔧 Developer Experience       🎯 Template Ecosystem  
Hot reload, instant testing,  Start with proven patterns.
rich tooling. Build fast.     Customer service, coding,
                              research, and more.

⚡ Performance Optimized      🔒 Enterprise Ready
Blazing fast on modern        Secure packaging, audit
hardware with local models.   trails, compliance friendly.
```

### **5. Getting Started**
```
[Heading] Deploy Your First AI Agent

[Code Block - Terminal Style]
# Install l6e AI
$ pip install l6e-forge

# Create and customize your agent
$ l6e create my-agent --template=assistant
$ # Edit my-agent/agent.py with your logic

# Test locally
$ l6e chat my-agent

# Package for deployment
$ l6e package my-agent
📦 Created my-agent.l6e (portable agent)

# Deploy anywhere
$ l6e deploy my-agent.l6e
🚀 Agent running locally

[Distribution Options]
💻 Local Deployment          🏢 Enterprise Install        🌐 Edge Distribution
Run on developer            Deploy to secure             Distribute to remote
machines and servers         enterprise infrastructure     locations and devices

[CTA Button] View Full Documentation
```

### **6. Community Section**
```
[Heading] Join the Local AI Revolution

[Cards Layout]
📚 Documentation          💬 Discord Community
Comprehensive guides       Join 500+ developers,
for agents and            enterprises, and AI
deployment               practitioners

⭐ GitHub Repository      📧 Newsletter
Star, contribute, and     Weekly updates on
report issues             local AI deployment

🏢 Enterprise Support    🌐 Agent Marketplace
Get help deploying       Discover and share
AI in your organization   packaged agents

[GitHub Stats Display]
⭐ 2.5k stars  🍴 200 forks  📦 150+ agent packages

[Newsletter Signup]
Email: [input field] [Subscribe Button]
"Get weekly insights on local AI deployment"
```

## 💻 Technical Requirements

### **Framework & Hosting**
- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Deploy on Vercel** (fast, developer-friendly)

### **Performance Requirements**
- **Lighthouse Score**: 95+ on all metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Mobile Performance**: 90+ score

### **Key Features**
- **Dark/Light mode toggle** (persistent)
- **Responsive design** (mobile-first)
- **Smooth scrolling** navigation
- **Code syntax highlighting** (Prism.js)
- **Auto-typing terminal** animation
- **GitHub star count** (live API)
- **Analytics** (Vercel Analytics)

## 🎬 Animations & Interactions

### **Hero Terminal Animation**
```javascript
// Auto-typing effect for terminal demo
const commands = [
  'pip install l6e-forge',
  'l6e init my-agents', 
  'l6e create assistant --template=personal',
  'l6e dev'
];

// Type each command with realistic delays
// Show realistic output after each command
// Loop after completion
```

### **Scroll Animations**
- **Fade in on scroll** for section content
- **Number counters** for statistics
- **Progress indicators** for getting started steps
- **Parallax effects** (subtle, performance-conscious)

### **Interactive Elements**
- **Hover effects** on buttons and cards
- **Click animations** for CTAs
- **Loading states** for dynamic content
- **Smooth transitions** between dark/light modes

## 📊 Analytics & Tracking

### **Goal Tracking**
- **Primary**: GitHub repository visits
- **Secondary**: Documentation page views  
- **Tertiary**: Newsletter signups
- **Downloads**: Track via GitHub releases API

### **User Flow Analysis**
- **Heat maps** on key sections
- **Scroll depth** tracking
- **Time on page** metrics
- **Conversion rates** for CTAs

## 🔍 SEO Requirements

### **Meta Tags**
```html
<title>l6e AI - Portable AI Agents | Localize AI for Any Machine</title>
<meta name="description" content="Create portable AI agents that run anywhere. l6e AI lets you build, package, and deploy AI on any machine. No cloud required, complete data sovereignty.">
<meta name="keywords" content="local AI, portable AI agents, AI deployment, edge AI, private AI, enterprise AI, AI infrastructure">

<!-- Open Graph -->
<meta property="og:title" content="l6e AI - Portable AI Agents for Any Machine">
<meta property="og:description" content="Build, package, and deploy AI agents anywhere. Complete data sovereignty with portable AI.">
<meta property="og:image" content="/og-image.png">
<meta property="og:url" content="https://l6e.ai">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="l6e AI - Portable AI Agents">
<meta name="twitter:description" content="Create AI agents that run anywhere. Build once, deploy everywhere.">
<meta name="twitter:image" content="/twitter-image.png">
```

### **Schema Markup**
- **SoftwareApplication** schema
- **Organization** schema for Localize AI
- **FAQ** schema for common questions

## 🎯 Conversion Optimization

### **Primary CTAs**
1. **"Get Started"** → GitHub repository
2. **"View Documentation"** → Docs site
3. **"Join Discord"** → Community

### **Secondary CTAs**
1. **Newsletter signup** → Email collection
2. **GitHub star** → Social proof
3. **Twitter follow** → Social growth

### **Social Proof Elements**
- **GitHub star count** (live)
- **Download statistics** 
- **Developer testimonials** (future)
- **Company logos** using l6e (future)

## 📱 Mobile Experience

### **Mobile-Specific Optimizations**
- **Touch-friendly** button sizes (44px minimum)
- **Readable typography** (16px+ base font)
- **Fast loading** on mobile networks
- **Swipe gestures** for navigation
- **Collapsible navigation** menu

### **Progressive Enhancement**
- **Core content** loads first
- **Animations** degrade gracefully
- **Offline capability** for key pages
- **Service Worker** for caching

## 🚀 Implementation Priority

### **Phase 1: MVP (Week 1)**
- Hero section with value prop
- Getting started guide
- Basic responsive layout
- Dark mode support

### **Phase 2: Enhanced (Week 2)**
- Live demo section
- Community section
- Animations and interactions
- Performance optimization

### **Phase 3: Advanced (Week 3)**
- Analytics implementation
- SEO optimization
- A/B testing setup
- Advanced animations

---

**Goal**: Create a marketing site that makes developers immediately want to try l6e/forge. Focus on clear value proposition, beautiful design, and seamless developer experience.