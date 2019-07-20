import unittest

from airflow.models import DagBag


class TestDags(unittest.TestCase):
    """
    Generic tests that all DAGs in the repository should be able to pass.
    """
    LOAD_SECOND_THRESHOLD = 2

    def setUp(self):
        self.dagbag = DagBag()

    def test_dagbag_import(self):
        """
        Verify that Airflow will be able to import all DAGs in the repository.
        """
        self.assertFalse(
            len(self.dagbag.import_errors),
            'There should be no DAG failures. Got: {}'.format(
                self.dagbag.import_errors
            )
        )

    def test_dagbag_import_time(self):
        """
        Verify that files describing DAGs load fast enough
        """
        stats = self.dagbag.dagbag_stats
        slow_files = filter(lambda d: d.duration > self.LOAD_SECOND_THRESHOLD, stats)
        res = ', '.join(map(lambda d: d.file[1:], slow_files))

        self.assertEqual(
            0,
            len(list(slow_files)),
            'The following files take more than {threshold}s to load: {res}'.format(
                threshold=self.LOAD_SECOND_THRESHOLD,
                res=res
            )
        )

    def test_dagbag_has_emails(self):
        """
        Verify that every DAG register alerts to the appropriate email address
        """
        for dag_id, dag in self.dagbag.dags.items():
            email_list = dag.default_args.get('email', [])
            msg = 'Alerts are not sent for DAG {id}'.format(id=dag_id)
            self.assertNotEqual(email_list, [], msg)

    def test_dagbag_has_owner(self):
        """
        Verify that every DAG has an owner
        """
        for dag_id, dag in self.dagbag.dags.items():
            owner = dag.default_args.get('owner', [])
            msg = '"owner" is not sent for DAG {id}'.format(id=dag_id)
            self.assertNotEqual(owner, [], msg)
