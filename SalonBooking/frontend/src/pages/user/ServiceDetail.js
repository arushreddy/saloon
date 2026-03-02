import React from 'react';
import { useParams, Link } from 'react-router-dom';

function ServiceDetail() {
  const { id } = useParams();
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">Service Detail</h1>
      <Link to={`/book/${id}`} className="bg-primary text-white px-6 py-3 rounded-lg font-bold">Book Now →</Link>
    </div>
  );
}

export default ServiceDetail;