"use client";

import { ContratType } from "@/types";

interface FiltersRowProps {
  activeType: ContratType;
  count: number;
  onType: (t: ContratType) => void;
  onReset: () => void;
}

export default function FiltersRow({
  activeType,
  count,
  onType,
  onReset,
}: Readonly<FiltersRowProps>) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: ".6rem",
        padding: ".8rem 2rem",
        flexWrap: "wrap",
      }}
    >
      <span
        style={{
          fontSize: ".8rem",
          fontWeight: 600,
          color: "var(--muted)",
          marginRight: ".2rem",
        }}
      >
        Type :
      </span>

      <Chip
        label="Tous"
        active={activeType === "all"}
        activeClass="all"
        onClick={() => onType("all")}
      />
      <Chip
        label="Achat"
        active={activeType === "achat"}
        activeClass="achat"
        dot="achat"
        onClick={() => onType("achat")}
      />
      <Chip
        label="LLD disponible"
        active={activeType === "lld"}
        activeClass="lld"
        dot="lld"
        onClick={() => onType("lld")}
      />

      <span
        style={{
          marginLeft: "auto",
          fontSize: ".82rem",
          color: "var(--muted)",
        }}
      >
        {count} véhicule{count > 1 ? "s" : ""}
      </span>

      <span
        onClick={onReset}
        style={{
          fontSize: ".8rem",
          color: "var(--cyan)",
          cursor: "pointer",
          textDecoration: "underline",
        }}
      >
        Réinitialiser les filtres
      </span>
    </div>
  );
}

function Chip({
  label,
  active,
  activeClass,
  dot,
  onClick,
}: {
  label: string;
  active: boolean;
  activeClass: "all" | "achat" | "lld";
  dot?: "achat" | "lld";
  onClick: () => void;
}) {
  const styles: Record<string, React.CSSProperties> = {
    base: {
      display: "inline-flex",
      alignItems: "center",
      gap: ".4rem",
      padding: ".38rem .9rem",
      borderRadius: "20px",
      fontSize: ".8rem",
      fontWeight: 500,
      cursor: "pointer",
      userSelect: "none",
      border: "1px solid var(--border)",
      background: "var(--white)",
      color: "var(--navy)",
      transition: "all .2s",
    },
    all: {
      background: "var(--navy)",
      color: "var(--white)",
      border: "1px solid var(--navy)",
    },
    achat: {
      background: "#EAF3DE",
      color: "#27500A",
      border: "1px solid #C0DD97",
    },
    lld: {
      background: "#E6F1FB",
      color: "#0C447C",
      border: "1px solid #85B7EB",
    },
  };

  const dotColors = { achat: "#639922", lld: "#185FA5" };

  return (
    <div
      onClick={onClick}
      style={active ? { ...styles.base, ...styles[activeClass] } : styles.base}
    >
      {dot && (
        <span
          style={{
            width: "7px",
            height: "7px",
            borderRadius: "50%",
            flexShrink: 0,
            background: dotColors[dot],
          }}
        />
      )}
      {label}
    </div>
  );
}
