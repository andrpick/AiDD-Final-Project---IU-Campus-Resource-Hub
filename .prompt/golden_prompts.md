# Golden Prompts

Effective prompts used during development. These are the top 25 most impactful prompts/agent actions that were key to the development of this web app.

## Project Creation
- "Build the application specified in PRD_COMPLETE.md and return me a simple list of steps"

## Core Features & Architecture

### 1. Database Schema Documentation
**Interaction #3** (see dev_notes.md)
**Prompt:** "Generate an ERD and Database Schema for this web app."
**Impact:** Created comprehensive ERD and Database Schema documentation, establishing foundation for all database-related work.

### 2. Code Refactoring - Initial
**Interaction #11** (see dev_notes.md)
**Prompt:** "You are an expert software developer, refactor the codebase looking for potential enhancements, etc."
**Impact:** Created controller_helpers.py and query_builder.py utility modules, reduced code duplication by ~50 lines, established reusable patterns.

### 3. Code Refactoring - Advanced
**Interaction #58** (see dev_notes.md)
**Prompt:** "You are an expert software programmer who has 30 years of experience developing web applications. refactor the codebase looking for redundant code, unused code, and check for improvements that can be made. Beware to not break the web app."
**Impact:** Extracted duplicate booking categorization logic, admin logging patterns, filter parsing helpers. Reduced code duplication by ~140 lines total, improved maintainability.

### 4. Test Implementation
**Interaction #16** (see dev_notes.md)
**Prompt:** "I like your recommendations, implement tests for the new utility modules."
**Impact:** Created comprehensive test suites for controller_helpers.py (37 tests) and query_builder.py (50 tests), bringing total test count to 139 tests with 100% pass rate.

### 5. Soft Delete Implementation
**Interaction #21** (see dev_notes.md)
**Prompt:** "What is best practice when dealing with deleted content in web apps?" followed by "Yes"
**Impact:** Implemented soft delete for users with PII anonymization, updated all user queries across services, preserved referential integrity. Major architectural improvement.

### 6. Resource Ownership Reassignment
**Interaction #23** (see dev_notes.md)
**Prompt:** "When a user is deleted and the resources they own are archived, the admin should have the ability to reassign ownership of the resource to either themself or another user."
**Impact:** Added admin-only resource ownership reassignment feature with proper security layers and audit logging.

### 7. Data Restore Page
**Interaction #36** (see dev_notes.md)
**Prompt:** "Proceed with adding a new Data Restore page and card for users and messages."
**Impact:** Created centralized Data Restore page for admin to restore deleted users and threads, improving data recovery capabilities.

### 8. Resource-Specific Operating Hours
**Interaction #60** (see dev_notes.md)
**Prompt:** "Add a feature so that the admin/owner of a resource can set the hours a the resource is available. We are doing away with the 8am-10pm hours and letting the admin and owners specify the hours."
**Impact:** Implemented resource-specific operating hours with 24-hour operation option, updated booking validation, calendar service, and all related services.

### 9. Profile Image Upload with Cropping
**Interaction #45** (see dev_notes.md)
**Prompt:** "When a profile image is uploaded, it should appear where the 'A' appears and users should be able to crop it to fit in the circle better."
**Impact:** Implemented profile image upload with Cropper.js integration, 1:1 aspect ratio cropping, automatic resizing to 400x400px. All user types can upload profile pictures.

### 10. Availability Date/Time Filtering
**Interaction #84** (see dev_notes.md)
**Prompt:** "Instead of a 24 hours or limited hours flag option, the user should be able to check to see what resources are available on a specific date and within a window of time."
**Impact:** Replaced simple flag filter with sophisticated availability checking that considers operating hours and existing bookings, major search enhancement.

### 11. Drag-and-Select Time Picker
**Interaction #87** (see dev_notes.md)
**Prompt:** "For start time, and end time, can we do a drag and select like feature to choose the time window? Similar to the drag and select for choosing a window of time to book."
**Impact:** Implemented visual drag-and-select time picker for availability filtering, significantly improving UX for time selection.

### 12. Booking Status "In Progress"
**Interaction #103** (see dev_notes.md)
**Prompt:** "Lets add booking status for 'In Progress'. If a booking is currently active, it should display 'In Progress'."
**Impact:** Added computed "In Progress" status for active bookings, updated all booking displays across the app, added filter option.

### 13. AI Assistant Named "Crimson"
**Interaction #106** (see dev_notes.md)
**Prompt:** "Lets give a name to the AI Assistant and call it 'Crimson'."
**Impact:** Renamed AI assistant to "Crimson" across all user-facing references, aligning with Indiana University branding.

### 14. Filter Modals Across Admin Pages
**Interaction #124** (see dev_notes.md)
**Prompt:** "Lets bring the filter modal to the rest of the admin dashboard pages with filtering options."
**Impact:** Converted all admin pages (Resources, Bookings, Logs, Statistics) to use consistent filter modal pattern, improving UI consistency and UX.

### 15. Markdown Rendering in AI Responses
**Interaction #137** (see dev_notes.md)
**Prompt:** "Why are there '**'s in Crimson's response?"
**Impact:** Implemented markdown-to-HTML conversion for AI responses, enabling bold/italic formatting in chatbot messages.

### 16. Chat History Persistence
**Interaction #138** (see dev_notes.md)
**Prompt:** "I went to a new page but shouldn't the chat history persist?"
**Impact:** Fixed chat history persistence across page navigations using localStorage, improving user experience.

### 17. Multiple Reviews Per Completed Booking
**Interaction #139** (see dev_notes.md)
**Prompt:** "Could we allow the user to review a resource as many times as they have had a completed booking for the resource?"
**Impact:** Removed UNIQUE constraint on reviews table, implemented business logic allowing one review per completed booking, major feature enhancement.

## UI/UX Improvements

### 18. UI/UX Standardization
**Interaction #109** (see dev_notes.md)
**Prompt:** "I want to standardize the UI/UX across pages for this web app. Things like the static shadow effect, button hover effect, etc. should be the same across pages. Also review logic for when the window of the webpage changes."
**Impact:** Created standardized shadow utility classes, standardized button hover effects, added comprehensive responsive media queries, fixed responsive design issues across all pages.

### 19. UI Standardization - Filter/Sort Boxes
**Interaction #100** (see dev_notes.md)
**Prompt:** "You are an UI/UX expert review all filter/sort boxes and adjust the field input boxes, 'Apply', and 'Reset' buttons to be the same height and font size. I am looking to standardize the UI across the web app."
**Impact:** Standardized all filter/sort boxes across the app with consistent form inputs, buttons, labels, and spacing. Professional appearance improvement.

### 20. Management Card Styling
**Interaction #9** (see dev_notes.md)
**Prompt:** "I like the style of the user management, resource management, booking management, and admin logs cards. Implement those styles to other cards in this webapp."
**Impact:** Applied consistent management card styling to empty states and call-to-action cards throughout the app, improving visual consistency.

## Search & Filtering Enhancements

### 21. Filter and Sort Options for Resources
**Interaction #81** (see dev_notes.md)
**Prompt:** "On the resources page, add a filter option for operating hours and allow the resources to be sorted by most booked, top rated (average), and recently booked."
**Impact:** Added operating hours filter and statistics-based sorting (booking_count, avg_rating, recently_booked) to both admin and public search pages.

### 22. Past Date/Time Validation
**Interaction #118** (see dev_notes.md)
**Prompt:** "Since 11/08/2025 1AM-2:30AM is in the past, a user should not be able to filter for this."
**Impact:** Added validation to prevent filtering for past dates/times, improving data quality and user experience.

### 23. Clear All Filters Functionality
**Interaction #119** (see dev_notes.md)
**Prompt:** "Add a clear all filters button to this page under the 'Filter' button. Currently the user has to clear applied filters one by one, I want to keep that but also allow the user to clear all at once."
**Impact:** Added "Clear All Filters" functionality across all pages with filter modals, improving UX for filter management.

## Bug Fixes & Error Handling

### 24. Fix Linting Errors
**Interaction #10** (see dev_notes.md)
**Prompt:** "Fix any errors in any files."
**Impact:** Fixed 4 syntax errors in JavaScript file, ensuring codebase is error-free and maintainable.

### 25. Documentation Review and Update
**Interaction #140** (see dev_notes.md)
**Prompt:** "Create a plan to review and refactor @AiDD-Final-Project---IU-Campus-Resource-Hub. I want all documentation files to be updated to reflect the current state of the web app."
**Impact:** Comprehensive documentation review and update across all files (README.md, SETUP_STEPS.md, PRD_COMPLETE.md, ERD_AND_SCHEMA.md), ensuring documentation accuracy.

## Notes
- Use specific, actionable prompts
- Reference existing documentation when available
- Break complex tasks into smaller steps
- Ask for expert perspective when refactoring ("You are an expert software developer...")
- Request comprehensive reviews when standardizing ("You are an UI/UX expert review all...")
- Log all interactions for transparency and future reference
