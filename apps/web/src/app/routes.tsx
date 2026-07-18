import { Navigate, Route, Routes } from "react-router-dom";

import { HomePage } from "../pages/HomePage";
import { AirspacesPage } from "../pages/AirspacesPage";
import { CrossingTrafficIntroPage } from "../pages/CrossingTrafficIntroPage";
import { CrossingTrafficLearnPage } from "../pages/CrossingTrafficLearnPage";
import { CrossingTrafficPracticeIntroPage } from "../pages/CrossingTrafficPracticeIntroPage";
import { CrossingTrafficPractice2IntroPage } from "../pages/CrossingTrafficPractice2IntroPage";
import { ConceptPage } from "../pages/ConceptPage";
import { HeadingVersusRadialLessonPage } from "../pages/HeadingVersusRadialLessonPage";
import { LearnPage } from "../pages/LearnPage";
import { LessonRunnerPage } from "../pages/LessonRunnerPage";
import { RunDetailPage } from "../pages/RunDetailPage";
import { RunsPage } from "../pages/RunsPage";
import { ScenariosPage } from "../pages/ScenariosPage";
import { SimulatePage } from "../pages/SimulatePage";
import { SimulateBriefPage } from "../pages/SimulateBriefPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/airspaces" element={<AirspacesPage />} />
      <Route path="/lessons" element={<LearnPage />} />
      <Route path="/learn/:conceptId" element={<ConceptPage />} />
      <Route path="/learn/:conceptId/:lessonId" element={<LessonRunnerPage />} />
      <Route path="/lessons/crossing-traffic" element={<CrossingTrafficIntroPage />} />
      <Route path="/lessons/crossing-traffic/learn" element={<CrossingTrafficLearnPage />} />
      <Route
        path="/lessons/crossing-traffic/practice"
        element={<CrossingTrafficPracticeIntroPage />}
      />
      <Route
        path="/lessons/crossing-traffic/practice-2"
        element={<CrossingTrafficPractice2IntroPage />}
      />
      <Route
        path="/lessons/heading-versus-radial"
        element={<HeadingVersusRadialLessonPage />}
      />
      <Route path="/scenarios" element={<ScenariosPage />} />
      <Route path="/simulate" element={<SimulatePage />} />
      <Route path="/simulate/:scenarioSlug" element={<SimulateBriefPage />} />
      <Route path="/runs" element={<RunsPage />} />
      <Route path="/runs/:runId" element={<RunDetailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
