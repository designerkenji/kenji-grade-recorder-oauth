/**
 * @fileoverview
 * Provides methods for the UI and interaction with the Grade Recorder Endpoints API.
 *
 * @author fisherds@google.com (Dave Fisher)
 */

/** namespace. */
var rh = rh || {};
rh.gr = rh.gr || {};

/**
 * Current assignment id being viewed.
 * @type {string}
 */
rh.gr.currentAssignmentKey = null;

/**
 * Enables the button callbacks in the UI.
 */
rh.gr.enableButtons = function() {
	$('#add-student-modal').on('shown.bs.modal', function() {
		$("input[name='first_name']").focus();
	});

	$('#add-assignment-modal').on('shown.bs.modal', function() {
		$("input[name='assignment_name']").focus();
	});

	$('#add-grade-entry-modal').on('shown.bs.modal', function() {
		// CONSIDER: Attempt to guess the next student needing a grade.
		if (rh.gr.currentAssignmentKey.length > 0) {
			$("select[name=assignment_key]").val(rh.gr.currentAssignmentKey);
		}
		$("input[name='score']").focus();
	});

	$("#toggle-edit-assignments").click(function() {
		$(".assignment-actions").toggleClass("hidden");
	});

	// Within Grade entry modal.
	$('.btn-toggle').click(function() {
		rh.gr.toggleGradeEntryModeSwitchDisplay();
	});

	$("#toggle-edit-grade-entries").click(function() {
		$(".grade-entry-actions").toggleClass("hidden");
		$("#grade-edits-complete").toggleClass("hidden");
	});

	$("#grade-edits-complete").click(function() {
		$(".grade-entry-actions").addClass("hidden");
		$("#grade-edits-complete").addClass("hidden");
	});

	$("#add-grade-by-student").click(function() {
		$("#grade-entry-type-input").val("SingleGradeEntry");
		$("#grade-entry-by-student-form-group").show();
		$("#grade-entry-by-team-form-group").hide();
	});

	$("#add-grade-by-team").click(function() {
		$("#grade-entry-type-input").val("TeamGradeEntry");
		$("#grade-entry-by-student-form-group").hide();
		$("#grade-entry-by-team-form-group").show();
	});

	$("#bulk-import-file-upload-button").click(
			function() {
				$("#bulk-import-file-upload-chooser")
						.attr("accept", "text/csv").trigger("click");
			});

	$(".edit-student").click(function() {
		firstName = $(this).find(".first-name").html();
		lastName = $(this).find(".last-name").html();
		roseUsername = $(this).find(".rose-username").html();
		team = $(this).find(".team").html();
		$("#add-student-modal input[name=first_name]").val(firstName);
		$("#add-student-modal input[name=last_name]").val(lastName);
		$("#add-student-modal input[name=rose_username]").val(roseUsername);
		$("#add-student-modal input[name=team]").val(team);
		$("#add-student-modal-title").html("Update student info");
		localStorage.showStudentEditDeleteTable = "yes";
	});

	$(".delete-student").click(function() {
		firstName = $(this).find(".first-name").html();
		lastName = $(this).find(".last-name").html();
		entityKey = $(this).find(".entity-key").html();
		$("#delete-student-name").html(firstName + " " + lastName);
		$("input[name=student_to_delete_key]").val(entityKey);

		if (entityKey == "AllStudents") {
			$("#delete-student-modal-title").html("Delete ALL Students!");
			$("#delete-student-modal .single-delete-text").hide();
		} else {
			localStorage.showStudentEditDeleteTable = "yes";
			$("#delete-student-modal .all-delete-text").hide();
		}
	});

	$(".edit-assignment").click(function() {
		name = $(this).find(".name").html();
		entityKey = $(this).find(".entity-key").html();
		$("#add-assignment-modal input[name=assignment_name]").val(name);
		$("#add-assignment-modal input[name=assignment_entity_key]").val(entityKey);
	});

	$(".delete-assignment").click(function() {
		name = $(this).find(".name").html();
		entityKey = $(this).find(".entity-key").html();
		$("#delete-assignment-name").html(name);
		$("input[name=assignment_to_delete_key]").val(entityKey);
	});

	$(".edit-grade-entry").click(function() {
		studentEntityKey = $(this).find(".student-key").html();
		assignmentEntityKey = $(this).find(".assignment-key").html();
		score = $(this).find(".score").html();
		rh.gr.currentAssignmentKey = assignmentEntityKey; // used in show event
		$("select[name=student_key]").val(studentEntityKey);
		$("input[name='score']").attr("placeholder", score);

		// In the Highly unlikely event Grade Entry is in Team mode.
		if ($("#add-grade-by-team").hasClass("active")) {
			rh.gr.toggleGradeEntryModeSwitchDisplay();
			$("#grade-entry-type-input").val("SingleGradeEntry");
			$("#grade-entry-by-student-form-group").show();
			$("#grade-entry-by-team-form-group").hide();
		}
	});

	$(".delete-grade-entry").click(function() {
		entityKey = $(this).find(".entity-key").html();
		$("input[name=grade_entry_to_delete_key]").val(entityKey);
		localStorage.showGradeEntryEditDelete = "yes";
		$("#delete-grade-entry-form").submit();
	});

	$("#select-all-student-fields").click(function() {
		$("#student-fields-export-table input[type=checkbox]").prop("checked", true);
	});

	$("#select-all-assignments").click(function() {
		$("#assignments-export-table input[type=checkbox]").prop("checked", true);
	});

	$("#download-csv").click(function() {
		$("#export-grades-modal").removeClass("fade").modal("hide");
	});
};

rh.gr.updateTable = function() {
	var table = $('#grade-entry-table').DataTable();
	table.search(rh.gr.currentAssignmentKey).draw();
};

rh.gr.updatePageTitle = function() {
	newName = $("#" + rh.gr.currentAssignmentKey).find(".assignment-name").html();
	if (newName) {
		$("#assignment-name").html(newName);
	} else {
		$("#assignment-name").html("Grades");
	}
};

// Toggle from Team grade entry to Student grade entry.
rh.gr.toggleGradeEntryModeSwitchDisplay = function() {
	// Change which button is "active primary" vs "default"
	$('.btn-toggle').find('.btn').toggleClass('active');
	if ($('.btn-toggle').find('.btn-primary').size() > 0) {
		$('.btn-toggle').find('.btn').toggleClass('btn-primary');
	}
	$('.btn-toggle').find('.btn').toggleClass('btn-default');
};

// Navigation of grade entries.
$(document).ready(function() {
	rh.gr.enableButtons();
	rh.gr.currentAssignmentKey = $('.sidebar-link.active').attr('id');
	rh.gr.updateTable();
	rh.gr.updatePageTitle();
	$('.sidebar-link').click(function() {
		// Update the sidebar
		$('.sidebar-link').removeClass('active');
		$(this).addClass('active');
		// Update the list of grades shown in the table.
		rh.gr.currentAssignmentKey = $(this).attr('id');
		rh.gr.updateTable();
		$(".row-offcanvas").removeClass("active");
		rh.gr.updatePageTitle();
	});

	if (localStorage.showStudentEditDeleteTable) {
		$("#select-student-to-edit-modal").modal("show");
	    localStorage.removeItem("showStudentEditDeleteTable");
	};

	if (localStorage.showGradeEntryEditDelete) {
		// Make sure there are grades remaining before going into edit mode.
		if (!$("table .dataTables_empty").length) {
			$(".grade-entry-actions").removeClass("hidden");
			$("#grade-edits-complete").removeClass("hidden");
		}
	    localStorage.removeItem("showGradeEntryEditDelete");
	};
});
