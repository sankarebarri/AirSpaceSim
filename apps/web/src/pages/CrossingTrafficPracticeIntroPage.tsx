import { PracticeIntroScreen } from "../components/PracticeIntroScreen";

export function CrossingTrafficPracticeIntroPage() {
  return (
    <PracticeIntroScreen
      title="Crossing Traffic · Practice"
      paragraphs={[
        "A similar traffic situation will develop. This time, identify the conflict and resolve it yourself. Maintain the required separation between all aircraft.",
      ]}
      scenarioId="crossing_traffic_practice"
      lessonId="enroute_crossing_traffic_intro"
      runName="Crossing Traffic Practice"
    />
  );
}
