// 백엔드 미가동/지연 시 데모 폴백을 위한 타임아웃 래퍼
export function withTimeout<T>(p: Promise<T>, ms = 2000): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}
