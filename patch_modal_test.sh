sed -i -e "/await screen.findByRole('option', { name: 'Alice Johnson' });/i \\
    fireEvent.click(screen.getByRole('tab', { name: 'Assignment & Automation' }));" enduser-ui-fe/src/components/TaskModal.test.tsx
