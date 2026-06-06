type Mode = "general" | "autoimmune";

interface HomeHeaderProps {
  name: string;
  mode: Mode;
}

export default function HomeHeader({ name, mode }: HomeHeaderProps) {
  return (
    <h1 className="text-3xl font-bold leading-tight">
      안녕하세요!
      <br />
      {name || "OOO"}님{" "}
      {mode === "general" ? (
        <span className="text-base font-semibold text-primary">일반 환자</span>
      ) : (
        <span className="text-base font-semibold" style={{ color: "#7C5CCF" }}>
          자가면역 환자
        </span>
      )}
    </h1>
  );
}