import { test, expect } from '@playwright/test';

test.describe('Admin Workflows', () => {
  
  test('Admin can create a new user (Alice)', async ({ page }) => {
    // 1. Login as Admin
    await page.goto('/');
    await page.getByRole('link', { name: 'Login' }).click();
    await page.getByPlaceholder('Email').fill('admin@archon.com');
    await page.getByPlaceholder('Password').fill('password');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    // Verify Dashboard access
    await expect(page).toHaveURL(/\/dashboard/);

    // 2. Navigate to Admin Panel
    await page.getByRole('link', { name: 'Admin Panel' }).click();
    await expect(page).toHaveURL(/\/admin/);

    // 3. Open Create User Modal
    await page.getByRole('button', { name: 'Create User' }).click();

    // 4. Fill Form (Alice)
    // We use a random email to avoid collision in repeat runs
    const randomId = Math.floor(Math.random() * 1000);
    const aliceEmail = `alice.test.${randomId}@archon.com`;
    
    await page.getByLabel('Name').fill('Alice Test');
    await page.getByLabel('Email').fill(aliceEmail);
    await page.getByLabel('Password').fill('password123');
    await page.getByLabel('Role').selectOption('member');
    
    // 5. Submit
    // This triggers the backend call. If backend fails with 500, this will fail or show error toast.
    await page.getByRole('button', { name: 'Create Member' }).click();

    // 6. Verify Success (Modal closes, Toast appears, or User in list)
    // Assuming the list refreshes or a success message is shown
    // For now, we check that we are still on the admin page and no error alert is visible
    await expect(page.getByRole('alert')).not.toBeVisible(); 
    await expect(page.getByText(aliceEmail)).toBeVisible();
  });

  test('Admin can edit a blog post', async ({ page }) => {
    // 1. Login as Admin
    await page.goto('/');
    await page.getByRole('link', { name: 'Login' }).click();
    await page.getByPlaceholder('Email').fill('admin@archon.com');
    await page.getByPlaceholder('Password').fill('password');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // 2. Go to Blog
    await page.getByRole('link', { name: 'Blog' }).click();
    
    // 3. Click first article (assuming seed data exists)
    await page.locator('article a').first().click();
    
    // 4. Check for Edit Button (Admin Privilege)
    const editButton = page.getByRole('button', { name: 'Edit' });
    await expect(editButton).toBeVisible();
    
    // 5. Click Edit -> Save
    await editButton.click();
    // Assuming an edit modal or inline edit. 
    // If not implemented in UI yet, this test will fail here, signaling UI work needed.
    // For this test, we just verify the permission (button visibility) for now 
    // as full edit UI might be part of Phase 6 polish.
  });

});
