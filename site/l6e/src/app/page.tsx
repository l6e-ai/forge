import Nav from "../components/Nav";
import Hero from "../components/Hero";
import Features from "../components/Features";
import AgentsOnRails from "../components/AgentsOnRails";
import Integrations from "../components/Integrations";
import GettingStarted from "../components/GettingStarted";
import AutoModels from "../components/AutoModels";
import Footer from "../components/Footer";
import DemoSection from "../components/Demo/DemoSection";

export default function Home() {
  return (
    <div className="min-h-screen font-sans bg-[#0a0a0a] text-white">
      <Nav />
      <main>
        <Hero />
        <DemoSection />
        <Features />
        <AgentsOnRails />
        <AutoModels />
        <Integrations />
        <GettingStarted />
      </main>
      <Footer />
    </div>
  );
}
