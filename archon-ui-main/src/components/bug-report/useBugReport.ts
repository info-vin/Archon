import { useState } from "react";
import { useToast } from "../../features/shared/hooks/useToast";
import {
  bugReportService,
  BugContext,
  BugReportData,
} from "../../services/bugReportService";
import { copyToClipboard } from "../../features/shared/utils/clipboard";

export const useBugReport = (context: BugContext, _onClose: () => void) => {
  const [report, setReport] = useState<Omit<BugReportData, "context">>({
    title: `🐛 ${context.error.name}: ${context.error.message}`,
    description: "",
    stepsToReproduce: "",
    expectedBehavior: "",
    actualBehavior: context.error.message,
    severity: "medium",
    component: "not-sure",
  });

  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!report.description.trim()) {
      showToast(
        "Please provide a description of what you were trying to do",
        "error",
      );
      return;
    }

    setSubmitting(true);

    try {
      const bugReportData: BugReportData = {
        ...report,
        context,
      };

      const result = await bugReportService.submitBugReport(bugReportData);

      if (result.success) {
        setSubmitted(true);

        if (result.issueNumber) {
          showToast(
            `Bug report created! Issue #${result.issueNumber} - maintainers will review it soon.`,
            "success",
            8000,
          );
          if (result.issueUrl) {
            window.open(result.issueUrl, "_blank");
          }
        } else {
          showToast(
            "Opening GitHub to submit your bug report...",
            "success",
            5000,
          );
          if (result.issueUrl) {
            const newWindow = window.open(
              result.issueUrl,
              "_blank",
              "noopener,noreferrer",
            );
            if (!newWindow) {
              showToast(
                "Popup blocked! Please allow popups or click the link in the modal.",
                "warning",
                8000,
              );
            }
          }
        }
      } else {
        const formattedReport =
          bugReportService.formatReportForClipboard(bugReportData);
        const clipboardResult = await copyToClipboard(formattedReport);

        if (clipboardResult.success) {
          showToast(
            "Failed to create GitHub issue, but bug report was copied to clipboard. Please paste it in a new GitHub issue.",
            "warning",
            10000,
          );
        } else {
          showToast(
            "Failed to create GitHub issue and could not copy to clipboard. Please report manually.",
            "error",
            10000,
          );
        }
      }
    } catch (error) {
      console.error("Bug report submission failed:", error);
      showToast(
        "Failed to submit bug report. Please try again or report manually.",
        "error",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyToClipboard = async () => {
    const bugReportData: BugReportData = { ...report, context };
    const formattedReport =
      bugReportService.formatReportForClipboard(bugReportData);

    const result = await copyToClipboard(formattedReport);
    if (result.success) {
      showToast("Bug report copied to clipboard", "success");
    } else {
      showToast("Failed to copy to clipboard", "error");
    }
  };

  return {
    report,
    setReport,
    submitting,
    submitted,
    handleSubmit,
    handleCopyToClipboard,
  };
};
