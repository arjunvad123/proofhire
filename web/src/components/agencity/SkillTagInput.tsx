"use client";

import { useState, type KeyboardEvent } from "react";
import { X } from "lucide-react";

interface SkillTagInputProps {
  value: string[];
  onChange: (skills: string[]) => void;
  placeholder?: string;
}

export function SkillTagInput({
  value,
  onChange,
  placeholder = "Type a skill and press Enter",
}: SkillTagInputProps) {
  const [input, setInput] = useState("");

  function addSkill(raw: string) {
    const skill = raw.trim();
    if (skill && !value.includes(skill)) {
      onChange([...value, skill]);
    }
    setInput("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(input);
    }
    if (e.key === "Backspace" && !input && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  }

  function removeSkill(skill: string) {
    onChange(value.filter((s) => s !== skill));
  }

  return (
    <div className="flex flex-wrap gap-2 p-2 border border-slate-300 rounded-lg focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-transparent bg-white min-h-[42px]">
      {value.map((skill) => (
        <span
          key={skill}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-100 text-emerald-700 text-sm font-medium rounded-md"
        >
          {skill}
          <button
            type="button"
            onClick={() => removeSkill(skill)}
            className="hover:text-emerald-900 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => input && addSkill(input)}
        placeholder={value.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[120px] outline-none text-sm text-slate-700 bg-transparent py-1 px-1"
      />
    </div>
  );
}
