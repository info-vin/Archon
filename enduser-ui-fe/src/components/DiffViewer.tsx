// enduser-ui-fe/src/components/DiffViewer.tsx
import React from 'react';
// Note: There might be peer dependency warnings with React 19.
// We will proceed and validate its functionality during testing.
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer';

interface DiffViewerProps {
  oldCode: string;
  newCode: string;
  splitView?: boolean;
}

const DiffViewer: React.FC<DiffViewerProps> = ({ oldCode, newCode, splitView = true }) => {
  return (
    <div className="w-full border rounded-md overflow-hidden">
      <ReactDiffViewer
        oldValue={oldCode}
        newValue={newCode}
        splitView={splitView}
        compareMethod={DiffMethod.WORDS}
        styles={{
          variables: {
            dark: {
              diffViewerBackground: '#1E1E1E',
              gutterBackground: '#2E2E2E',
              addedBackground: '#043A04',
              removedBackground: '#5B0000',
            }
          }
        }}
        useDarkTheme={true}
      />
    </div>
  );
};

export default DiffViewer;
