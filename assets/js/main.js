const member = require('./member/main')

document.addEventListener("DOMContentLoaded", function() {

	const editMember = document.getElementById('edit_member')
	if (editMember) {
	  // if member template is loaded add listener to edit_member element
	  editMember.onclick = member.toggleEditMember
	}

	// open and close modal
	const memberModal = document.getElementById('create-member-modal')
	const createAccountBtn = document.getElementById('create-account-btn')
	const backdrop = document.getElementById('create-member-modal-backdrop')
	function openMemberModal() {
		memberModal.classList.add('show-modal')
	}
	function closeMemberModal() {
		memberModal.classList.remove('show-modal')
	}
	createAccountBtn.onclick = openMemberModal
	backdrop.onclick = closeMemberModal

})
