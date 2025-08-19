import Nav from "../components/Nav";
import Hero from "../components/Hero";
import Features from "../components/Features";
import GettingStarted from "../components/GettingStarted";
import Footer from "../components/Footer";

export default function Home() {
  return (
    <div className="min-h-screen font-sans bg-[#0a0a0a] text-white">
      <Nav />
      <main>
        <Hero />
        <Features />
        <GettingStarted />
      </main>
      <Footer />
    </div>
  );
}
