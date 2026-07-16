import { PracticeIntroScreen } from "../components/PracticeIntroScreen";

export function CrossingTrafficPractice2IntroPage() {
  return (
    <PracticeIntroScreen
      title="Crossing Traffic · Practice 2"
      paragraphs={[
        "Maintain the required separation between all aircraft.",
        "This time, no conflict information will be provided. Observe the traffic and intervene only when necessary.",
      ]}
      scenarioId="crossing_traffic_practice_2"
      lessonId="enroute_crossing_traffic_intro"
      runName="Crossing Traffic Practice 2"
    />
  );
}
