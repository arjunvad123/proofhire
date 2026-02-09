"use client";

import { useEffect, useRef, useState } from "react";

interface University {
  name: string;
  logoUrl: string;
}

export function UniversityCarousel() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const universities: University[] = [
    { name: "MIT", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/MIT_logo.svg/500px-MIT_logo.svg.png" },
    { name: "Stanford", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Seal_of_Leland_Stanford_Junior_University.svg/1200px-Seal_of_Leland_Stanford_Junior_University.svg.png" },
    { name: "UC Berkeley", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/a/a1/Seal_of_University_of_California%2C_Berkeley.svg" },
    { name: "Carnegie Mellon", logoUrl: "https://upload.wikimedia.org/wikipedia/en/thumb/b/bb/Carnegie_Mellon_University_seal.svg/1200px-Carnegie_Mellon_University_seal.svg.png" },
    { name: "Georgia Tech", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Georgia_Tech_seal.svg/1200px-Georgia_Tech_seal.svg.png" },
    { name: "UIUC", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/University_of_Illinois_seal.svg/1200px-University_of_Illinois_seal.svg.png" },
    { name: "Caltech", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Caltech_Logo.svg/330px-Caltech_Logo.svg.png" },
    { name: "UCLA", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/UCLA_Bruins_primary_logo.svg/1200px-UCLA_Bruins_primary_logo.svg.png" },
    { name: "Cornell", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Cornell_University_seal.svg/1200px-Cornell_University_seal.svg.png" },
    { name: "Waterloo", logoUrl: "https://upload.wikimedia.org/wikipedia/en/thumb/6/6e/University_of_Waterloo_seal.svg/1200px-University_of_Waterloo_seal.svg.png" },
  ];

  // Duplicate for seamless loop
  const allLogos = [...universities, ...universities, ...universities];

  return (
    <section className="py-8 overflow-hidden bg-white border-y border-zinc-100">
      <div className="mx-auto max-w-6xl px-4 mb-6">
        <h3 className="text-xs uppercase tracking-widest text-zinc-400 text-center sm:text-left">
          Engineers from top programs
        </h3>
      </div>

      <div
        className="relative w-full overflow-hidden"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Gradient masks for smooth edges */}
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />

        <div
          ref={scrollRef}
          className={`flex items-center gap-12 w-max ${isHovered ? '' : 'animate-scroll'}`}
          style={{
            animationPlayState: isHovered ? 'paused' : 'running',
          }}
        >
          {allLogos.map((university, index) => (
            <div
              key={`${university.name}-${index}`}
              className="flex-shrink-0 px-4 grayscale opacity-60 hover:grayscale-0 hover:opacity-100 transition-all duration-300"
            >
              <img
                src={university.logoUrl}
                alt={university.name}
                className="h-10 w-auto object-contain"
                loading="lazy"
                onError={(e) => {
                  // Hide broken images
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
