const member = require('./member/main')

const editMember = document.getElementById('edit_member')
if (editMember) {
  // if member template is loaded add listener to edit_member element
  editMember.onclick = member.toggleEditMember
}
