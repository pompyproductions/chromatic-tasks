# CHROMATIC Tasks | Project roadmap

--- 
## Current to-do list

### Pages

#### "Create task" page

- [ ] When submitting a new task with a date and without a "status"


### Modals

#### "Are you sure" modal

- [ ] Create "are you sure?" prompt when deleting a database entry
- [ ] Add "don't show this again" checkbox

#### "Edit Task" modal
- [ ] Display all values of selected task instance
- [ ] Update db entry and table view on submit
- [ ] If schedule is checked, date is valid, and status is Pending: change status to SCHEDULED on submit
  - [ ] When scheduled is checked & date is valid, option 1 turns from "PENDING" into "SCHEDULED"?


### Widgets

#### "DateInput" widget

- [ ] Add a "today" functionality to avoid entering the date manually (button?)

---

## Future functionality

### Task templates

- Create "task templates" that you can use to quickly create task instances

### Visualisation

Create either a sidebar or a modal for fine-grained control over table view.
- Sorting: multi-step, descending/ascending/list order for each (e.g. first by status, then schedule date...)
- Filtering: nothing new here
- Fixing: Certain rows can be fixed to stay "always on top".

Maybe also special flags like "highlight overdue tasks" or "overdue tasks always on top".

Ideally, since it's so fine grained, it should be "saved to disk" so that you can store/recall/share views.
