<h1>List Users</h1>
<table id="tbl-users-list" class="table table-bordered table-striped">
  <thead>
      <tr>
            <td colspan="5" align="right"><a href="<?= $this->Url->build('/users/add', ['fullBase' => true]) ?>">Add User</a></td>
       </tr>
      <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Email</th>
          <th>Phone No</th>
          <th>Action</th>
      </tr>
  </thead>
  <tbody>
      <?php
        if (count($users) > 0) {
            foreach ($users as $index => $data) {
        ?>
              <tr>
                  <td><?= $data->id ?></td>
                  <td><?= $data->name ?></td>
                  <td><?= $data->email ?></td>
                  <td><?= $data->phone_no ?></td>
                  <td>
                      <form id="frm-delete-user-<?= $data->id ?>" action="<?= $this->Url->build('/delete-user/' . $data->id, ['fullBase' => false]) ?>" method="post"><input type="hidden" value="<?= $data->id ?>" name="id" /></form>
                  </td>
              </tr>
      <?php
            }
        }
        ?>
  </tbody>
</table>
